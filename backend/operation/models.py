from django.conf import settings
from django.db import models


class Announcement(models.Model):
    TYPE_CHOICES = [
        ('notice', '通知'),
        ('activity', '活动'),
        ('urgent', '紧急'),
    ]

    title = models.CharField('标题', max_length=200)
    content = models.TextField('内容')
    type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES, default='notice')
    is_published = models.BooleanField('已发布', default=False)
    publish_time = models.DateTimeField('定时发布时间', null=True, blank=True)
    is_withdrawn = models.BooleanField('已撤回', default=False)
    is_archived = models.BooleanField('已归档', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'operation_announcement'
        verbose_name = '公告'
        verbose_name_plural = verbose_name
        ordering = ['-publish_time', '-created_at']

    def __str__(self):
        return self.title


class SystemLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs',
        verbose_name='用户',
    )
    action = models.CharField('操作类型', max_length=64)
    detail = models.TextField('详情', blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    created_at = models.DateTimeField('时间', auto_now_add=True)

    class Meta:
        db_table = 'operation_system_log'
        verbose_name = '系统日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} @ {self.created_at}'
