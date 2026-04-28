from django.db import models
from django.conf import settings


class RepairOrder(models.Model):
    """报修工单模型"""
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    property = models.ForeignKey('users.Property', on_delete=models.CASCADE, related_name='repair_orders', verbose_name='报修房产')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='repair_orders', verbose_name='报修人')
    description = models.TextField('故障描述')
    images = models.JSONField('现场图片', default=list, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_repairs',
        verbose_name='指派员工'
    )
    assigned_at = models.DateTimeField('分配时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'property_repair_order'
        verbose_name = '报修工单'
        verbose_name_plural = '报修工单'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"报修 {self.id}"


class Complaint(models.Model):
    """投诉建议模型"""
    TYPE_CHOICES = [
        ('service', '物业服务'),
        ('environment', '环境卫生'),
        ('security', '安全管理'),
        ('facility', '设施设备'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints', verbose_name='投诉人')
    type = models.CharField('投诉类型', max_length=20, choices=TYPE_CHOICES)
    title = models.CharField('标题', max_length=200)
    description = models.TextField('问题描述')
    images = models.JSONField('相关证据', default=list, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    handler = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='handled_complaints',
        verbose_name='处理人'
    )
    handler_remark = models.TextField('处理备注', blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'property_complaint'
        verbose_name = '投诉建议'
        verbose_name_plural = '投诉建议'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"投诉 {self.id} - {self.title}"


class ServiceFeedback(models.Model):
    """服务反馈模型"""
    RATING_CHOICES = [
        (1, '非常差'),
        (2, '差'),
        (3, '一般'),
        (4, '好'),
        (5, '非常好'),
    ]
    
    order = models.OneToOneField(RepairOrder, on_delete=models.CASCADE, related_name='feedback', verbose_name='关联工单')
    rating = models.IntegerField('评分', choices=RATING_CHOICES)
    comment = models.TextField('评价内容', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'property_service_feedback'
        verbose_name = '服务反馈'
        verbose_name_plural = '服务反馈'
    
    def __str__(self):
        return f"反馈 {self.id} - {self.rating}星"