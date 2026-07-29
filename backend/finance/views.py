import csv
import io
from datetime import date, timedelta

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from operation.utils import log_action
from users.models import Property

from .alipay_service import build_pay_url, finish_bill_from_alipay
from .models import Bill, ChargeItem, PaymentRecord
from .serializers import BillSerializer, ChargeItemSerializer, PaymentRecordSerializer


def _admin(u):
    return u.is_authenticated and (u.role == 'admin' or getattr(u, 'is_superuser', False))


def _owner(u):
    return u.is_authenticated and u.role == 'owner'


class ChargeItemViewSet(viewsets.ModelViewSet):
    queryset = ChargeItem.objects.all()
    serializer_class = ChargeItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset().order_by('id')
        if _admin(self.request.user):
            q = self.request.query_params.get('search')
            t = self.request.query_params.get('type')
            active = self.request.query_params.get('is_active')
            if q:
                qs = qs.filter(name__icontains=q)
            if t:
                qs = qs.filter(type=t)
            if active is not None:
                qs = qs.filter(is_active=(str(active).lower() in ('1', 'true', 'yes')))
            return qs
        return qs.filter(is_active=True)

    def update(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all().select_related('property', 'charge_item')
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if _admin(u):
            pid = self.request.query_params.get('property')
            bid = self.request.query_params.get('building')
            oid = self.request.query_params.get('owner')
            ym = self.request.query_params.get('year_month')
            st = self.request.query_params.get('status')
            cid = self.request.query_params.get('charge_item')
            q = self.request.query_params.get('search')
            if pid:
                qs = qs.filter(property_id=pid)
            if bid:
                qs = qs.filter(property__building_number=bid)
            if oid:
                qs = qs.filter(property__owner_id=oid)
            if ym:
                qs = qs.filter(year_month=ym)
            if st:
                qs = qs.filter(status=st)
            if cid:
                qs = qs.filter(charge_item_id=cid)
            if q:
                qs = qs.filter(
                    Q(property__room_number__icontains=q)
                    | Q(property__owner__username__icontains=q)
                    | Q(charge_item__name__icontains=q)
                )
            return qs
        if _owner(u):
            rooms = Property.objects.filter(owner=u, property_type='room')
            return qs.filter(property__in=rooms)
        return qs.none()

    def create(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        data = request.data.copy()
        property_id = data.get('property')
        charge_item_id = data.get('charge_item')
        year_month = (data.get('year_month') or '').strip()
        if not property_id or not charge_item_id:
            return Response({'detail': '请先选择房产和收费项目'}, status=status.HTTP_400_BAD_REQUEST)
        item = ChargeItem.objects.filter(pk=charge_item_id).first()
        if not item:
            return Response({'detail': '收费项目不存在'}, status=status.HTTP_400_BAD_REQUEST)
        if not year_month:
            year_month = date.today().strftime('%Y-%m')
        amount = data.get('amount')
        if amount in (None, ''):
            amount = item.unit_price
        due_date = data.get('due_date')
        if not due_date:
            due_date = (date.today() + timedelta(days=30)).isoformat()
        defaults = {
            'amount': amount,
            'status': data.get('status') or 'unpaid',
            'due_date': due_date,
            'remark': data.get('remark', ''),
        }
        obj, created = Bill.objects.update_or_create(
            property_id=property_id,
            charge_item_id=charge_item_id,
            year_month=year_month,
            defaults=defaults,
        )
        log_action(request, 'bill_create', f'{"新增" if created else "更新"}账单#{obj.id}')
        return Response(BillSerializer(obj).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        bill = self.get_object()
        if bill.status == 'paid':
            return Response({'detail': '该账单已缴费'}, status=status.HTTP_400_BAD_REQUEST)
        if _owner(request.user) and bill.property.owner_id != request.user.id:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        if not (_owner(request.user) or _admin(request.user)):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        method = request.data.get('payment_method', 'wechat')
        if method == 'alipay':
            pay_url, amount = build_pay_url(bill)
            log_action(request, 'bill_pay_alipay_start', f'账单#{bill.id}')
            return Response(
                {
                    'payment_method': 'alipay',
                    'pay_url': pay_url,
                    'out_trade_no': f'BILL-{bill.id}',
                    'amount': amount,
                    'bill': BillSerializer(bill).data,
                }
            )
        bill.status = 'paid'
        bill.paid_at = timezone.now()
        bill.save(update_fields=['status', 'paid_at'])
        PaymentRecord.objects.create(
            bill=bill,
            amount=bill.amount,
            payment_method=method,
            transaction_no=f'MOCK-{int(timezone.now().timestamp())}',
            operator=request.user,
        )
        log_action(request, 'bill_pay', f'账单#{bill.id}')
        return Response(BillSerializer(bill).data)
    

    @action(detail=False, methods=['post'], url_path='alipay/confirm')
    def alipay_confirm(self, request):
        result = finish_bill_from_alipay(request.data)
        if not result.get('ok'):
            query = result.get('query') or {}
            trade_status = query.get('trade_status')
            if trade_status in ('WAIT_BUYER_PAY', 'PAYING'):
                return Response(
                    {
                        'status': 'pending',
                        'detail': '支付宝交易处理中，请稍后再试',
                        'query': query,
                        'out_trade_no': result.get('out_trade_no'),
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
            if trade_status == 'TRADE_CLOSED':
                return Response(
                    {
                        'status': 'error',
                        'detail': query.get('sub_msg') or query.get('msg') or '支付宝交易已关闭',
                        'query': query,
                        'out_trade_no': result.get('out_trade_no'),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {'detail': result.get('detail', '支付宝支付确认失败'), 'query': result.get('query', {})},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bill = self.get_queryset().filter(pk=result['bill_id']).select_related('property', 'charge_item').first()
        if not bill:
            return Response({'detail': '账单不存在或无权限'}, status=status.HTTP_404_NOT_FOUND)
        trade_no = result.get('trade_no') or result.get('out_trade_no')
        payment, created = PaymentRecord.objects.get_or_create(
            bill=bill,
            payment_method='alipay',
            transaction_no=trade_no,
            defaults={
                'amount': bill.amount,
                'operator': request.user if request.user.is_authenticated else None,
                'remark': f'out_trade_no={result.get("out_trade_no", "")}',
            },
        )
        if not created and request.user.is_authenticated and payment.operator_id is None:
            payment.operator = request.user
            payment.save(update_fields=['operator'])
        if bill.status != 'paid':
            bill.status = 'paid'
            bill.paid_at = timezone.now()
            bill.save(update_fields=['status', 'paid_at'])
        log_action(request, 'bill_pay_alipay_finish', f'账单#{bill.id}')
        bill.refresh_from_db()
        return Response(
            {
                'status': 'success',
                'message': '支付宝支付确认成功',
                'bill': BillSerializer(bill).data,
                'payment': {
                    'id': payment.id,
                    'payment_method': payment.payment_method,
                    'transaction_no': payment.transaction_no,
                    'amount': str(payment.amount),
                },
                'trade_no': trade_no,
                'out_trade_no': result.get('out_trade_no'),
            }
        )

    @action(detail=False, methods=['post'])
    def generate(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        year_month = request.data.get('year_month') or date.today().strftime('%Y-%m')
        charge_item_id = request.data.get('charge_item')
        if not charge_item_id:
            return Response({'detail': '缺少 charge_item'}, status=status.HTTP_400_BAD_REQUEST)
        item = ChargeItem.objects.filter(pk=charge_item_id, is_active=True).first()
        if not item:
            return Response({'detail': '收费项目不存在'}, status=status.HTTP_400_BAD_REQUEST)
        due_raw = request.data.get('due_date') or date.today().isoformat()
        try:
            due = date.fromisoformat(str(due_raw)[:10])
        except ValueError:
            due = date.today()
        n = 0
        rooms = Property.objects.filter(property_type='room', status=True)
        for prop in rooms:
            _, created = Bill.objects.get_or_create(
                property=prop,
                charge_item=item,
                year_month=year_month,
                defaults={
                    'amount': item.unit_price,
                    'status': 'unpaid',
                    'due_date': due,
                },
            )
            if created:
                n += 1
        log_action(request, 'bill_generate', f'{year_month} 生成{n}条')
        return Response({'created': n, 'year_month': year_month})

    @action(detail=False, methods=['post'], url_path='generate-all')
    def generate_all(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        year_month = request.data.get('year_month') or date.today().strftime('%Y-%m')
        charge_item_id = request.data.get('charge_item')
        if not charge_item_id:
            return Response({'detail': '缺少 charge_item'}, status=status.HTTP_400_BAD_REQUEST)
        item = ChargeItem.objects.filter(pk=charge_item_id, is_active=True).first()
        if not item:
            return Response({'detail': '收费项目不存在或未启用'}, status=status.HTTP_400_BAD_REQUEST)
        due_raw = request.data.get('due_date') or date.today().isoformat()
        try:
            due = date.fromisoformat(str(due_raw)[:10])
        except ValueError:
            due = date.today()

        rooms = Property.objects.filter(property_type='room', status=True)
        total_targets = rooms.count()
        created_count = 0
        for prop in rooms:
            _, created = Bill.objects.get_or_create(
                property=prop,
                charge_item=item,
                year_month=year_month,
                defaults={
                    'amount': item.unit_price,
                    'status': 'unpaid',
                    'due_date': due,
                },
            )
            if created:
                created_count += 1

        skipped_count = total_targets - created_count
        log_action(
            request,
            'bill_generate_all',
            f'{year_month} {item.name} 全员收费，新建{created_count}条，跳过{skipped_count}条',
        )
        return Response(
            {
                'created': created_count,
                'skipped': skipped_count,
                'total_targets': total_targets,
                'year_month': year_month,
                'charge_item': item.id,
                'charge_item_name': item.name,
            }
        )

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        qs = Bill.objects.all().select_related('property', 'charge_item', 'property__owner')
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['账单ID', '房产', '收费项', '账期', '金额', '状态', '业主'])
        for b in qs:
            w.writerow(
                [
                    b.id,
                    str(b.property),
                    b.charge_item.name,
                    b.year_month,
                    b.amount,
                    b.get_status_display(),
                    b.property.owner.username if b.property.owner else '',
                ]
            )
        resp = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
        resp['Content-Disposition'] = 'attachment; filename="bills.csv"'
        log_action(request, 'bill_export', '导出账单')
        return resp

    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        rows = request.data.get('rows') or []
        if not isinstance(rows, list) or not rows:
            return Response({'detail': 'rows 必须是非空数组'}, status=status.HTTP_400_BAD_REQUEST)
        created = 0
        errors = []
        for idx, row in enumerate(rows, start=1):
            try:
                ser = BillSerializer(data=row)
                ser.is_valid(raise_exception=True)
                ser.save()
                created += 1
            except Exception as exc:
                errors.append(f'第{idx}行失败: {exc}')
        log_action(request, 'bill_batch_create', f'批量创建账单{created}条')
        return Response({'created': created, 'errors': errors})


class PaymentRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentRecord.objects.all().select_related('bill', 'operator')
    serializer_class = PaymentRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if _admin(self.request.user):
            return qs
        if _owner(self.request.user):
            rooms = Property.objects.filter(owner=self.request.user, property_type='room')
            return qs.filter(bill__property__in=rooms)
        return qs.none()
