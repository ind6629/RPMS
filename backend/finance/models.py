from django.db import models
from django.conf import settings


class ChargeItem(models.Model):
    """收费项目模型"""
    TYPE_CHOICES = [
        ('property_fee', '物业费'),
        ('parking_fee', '停车费'),
        ('water_fee', '水费'),
        ('electricity_fee', '电费'),
        ('gas_fee', '燃气费'),
        ('other', '其他'),
    ]
    
    name = models.CharField('项目名称', max_length=100)
    type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES)
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    unit = models.CharField('计量单位', max_length=20)
    description = models.TextField('描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'finance_charge_item'
        verbose_name= '收费项目'
        verbose_name_plural = '收费项目'
    
    def __str__(self):
        return self.name


class Bill(models.Model):
    """账单模型"""
    STATUS_CHOICES = [
        ('unpaid', '未缴费'),
        ('paid', '已缴费'),
        ('overdue', '已逾期'),
    ]
    
    property = models.ForeignKey('users.Property', on_delete=models.CASCADE, related_name='bills', verbose_name='关联房产')
    charge_item = models.ForeignKey(ChargeItem, on_delete=models.CASCADE, related_name='bills', verbose_name='收费项目')
    year_month = models.CharField('年份月份', max_length=7)
    amount = models.DecimalField('应缴金额', max_digits=10, decimal_places=2)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='unpaid')
    due_date = models.DateField('截止日期')
    paid_at = models.DateTimeField('缴费时间', null=True, blank=True)
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'finance_bill'
        verbose_name = '账单'
        verbose_name_plural = '账单'
        ordering = ['-year_month', '-created_at']
        unique_together = ['property', 'charge_item', 'year_month']
    
    def __str__(self):
        return f"{self.property} - {self.year_month} - {self.charge_item.name}"


class PaymentRecord(models.Model):
    """缴费记录模型"""
    METHOD_CHOICES = [
        ('wechat', '微信支付'),
        ('alipay', '支付宝'),
        ('bank', '银行转账'),
        ('cash', '现金'),
        ('other', '其他'),
    ]
    
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='payment_records', verbose_name='关联账单')
    amount = models.DecimalField('缴费金额', max_digits=10, decimal_places=2)
    payment_method = models.CharField('支付方式', max_length=20, choices=METHOD_CHOICES)
    transaction_no = models.CharField('交易流水号', max_length=100, blank=True)
    payment_time = models.DateTimeField('缴费时间', auto_now_add=True)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='payment_records',
        verbose_name='操作人'
    )
    remark = models.TextField('备注', blank=True)
    
    class Meta:
        db_table = 'finance_payment_record'
        verbose_name = '缴费记录'
        verbose_name_plural = '缴费记录'
        ordering = ['-payment_time']

    def __str__(self):
        return f"缴费 {self.id} - {self.bill}"