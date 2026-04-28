import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from alipay import AliPay
from django.conf import settings

from .models import Bill


def _require_config():
    missing = []
    for key in ('ALIPAY_APP_ID', 'ALIPAY_APP_PRIVATE_KEY', 'ALIPAY_PUBLIC_KEY', 'ALIPAY_GATEWAY'):
        if not getattr(settings, key, ''):
            missing.append(key)
    if missing:
        raise RuntimeError(f'支付宝配置缺失：{", ".join(missing)}')


def _client():
    _require_config()
    return AliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=settings.ALIPAY_NOTIFY_URL or None,
        app_private_key_string=settings.ALIPAY_APP_PRIVATE_KEY,
        alipay_public_key_string=settings.ALIPAY_PUBLIC_KEY,
        sign_type='RSA2',
        debug=settings.ALIPAY_DEBUG,
    )


def build_out_trade_no(bill: Bill) -> str:
    return f'BILL-{bill.id}'


def parse_bill_id(out_trade_no: str):
    if not out_trade_no:
        return None
    text = str(out_trade_no).strip()
    if text.startswith('BILL-'):
        text = text[5:]
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def build_pay_url(bill: Bill, return_url: Optional[str] = None):
    client = _client()
    total_amount = Decimal(bill.amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    order_string = client.api_alipay_trade_page_pay(
        subject=f'物业费用-{bill.year_month}-{bill.charge_item.name}',
        out_trade_no=build_out_trade_no(bill),
        total_amount=str(total_amount),
        return_url=return_url or settings.ALIPAY_RETURN_URL,
        notify_url=settings.ALIPAY_NOTIFY_URL or None,
    )
    gateway = settings.ALIPAY_GATEWAY.rstrip('?')
    return f'{gateway}?{order_string}', str(total_amount)


def verify_return_params(params: dict) -> bool:
    client = _client()
    data = dict(params or {})
    signature = data.pop('sign', '')
    data.pop('sign_type', None)
    if not signature:
        return False
    return client.verify(data, signature)


def query_trade(out_trade_no: str = '', trade_no: str = '') -> dict:
    client = _client()
    resp = client.api_alipay_trade_query(
        out_trade_no=out_trade_no or None,
        trade_no=trade_no or None,
    )
    if isinstance(resp, str):
        try:
            resp = json.loads(resp)
        except json.JSONDecodeError:
            return {}
    if not isinstance(resp, dict):
        return {}
    return resp.get('alipay_trade_query_response') or resp.get('response') or resp


def finish_bill_from_alipay(params: dict):
    if not verify_return_params(params):
        return {'ok': False, 'detail': '支付宝验签失败'}

    out_trade_no = str(params.get('out_trade_no') or '').strip()
    bill_id = parse_bill_id(out_trade_no)
    if not bill_id:
        return {'ok': False, 'detail': '订单号不合法'}

    bill = Bill.objects.select_related('property', 'charge_item').filter(pk=bill_id).first()
    if not bill:
        return {'ok': False, 'detail': '账单不存在'}

    trade_no = str(params.get('trade_no') or '').strip()
    query_data = query_trade(out_trade_no=out_trade_no, trade_no=trade_no)
    if query_data.get('code') != '10000' or query_data.get('trade_status') not in ('TRADE_SUCCESS', 'TRADE_FINISHED'):
        return {
            'ok': False,
            'detail': query_data.get('sub_msg') or query_data.get('msg') or '支付宝查询支付结果失败',
            'query': query_data,
        }

    return {
        'ok': True,
        'bill_id': bill.id,
        'year_month': bill.year_month,
        'amount': str(bill.amount),
        'trade_no': trade_no or query_data.get('trade_no') or out_trade_no,
        'out_trade_no': out_trade_no,
        'query': query_data,
    }
