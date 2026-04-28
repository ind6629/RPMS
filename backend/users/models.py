from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """自定义用户模型"""
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('employee', '员工'),
        ('owner', '业主'),
    ]
    
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='owner')
    phone = models.CharField('手机号', max_length=20, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    status = models.BooleanField('账号状态', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'sys_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.username


class UserProfile(models.Model):
    """用户详细信息"""
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES, blank=True)
    id_card = models.CharField('身份证号', max_length=18, blank=True)
    address = models.CharField('地址', max_length=255, blank=True)
    emergency_contact = models.CharField('紧急联系人', max_length=50, blank=True)
    emergency_phone = models.CharField('紧急联系电话', max_length=20, blank=True)
    
    class Meta:
        db_table = 'sys_user_profile'
        verbose_name = '用户详情'
        verbose_name_plural = verbose_name


class Property(models.Model):
    """房产信息"""
    PROPERTY_TYPE_CHOICES = [
        ('building', '楼栋'),
        ('unit', '单元'),
        ('room', '房屋'),
    ]
    
    name = models.CharField('名称', max_length=100)
    property_type = models.CharField('房产类型', max_length=20, choices=PROPERTY_TYPE_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    building_number = models.CharField('楼栋号', max_length=20, blank=True)
    unit_number = models.CharField('单元号', max_length=20, blank=True)
    room_number = models.CharField('房号', max_length=20, blank=True)
    area = models.DecimalField('面积(㎡)', max_digits=10, decimal_places=2, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='properties')
    status = models.BooleanField('状态', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'sys_property'
        verbose_name = '房产'
        verbose_name_plural = verbose_name
        ordering = ['property_type', 'building_number', 'unit_number', 'room_number']
    
    def __str__(self):
        return f"{self.building_number}-{self.unit_number}-{self.room_number}" if self.room_number else self.name