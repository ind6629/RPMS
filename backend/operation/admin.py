from django.contrib import admin
from .models import Announcement, SystemLog

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'type', 'is_published', 'publish_time', 'created_at']
    list_filter = ['type', 'is_published']
    search_fields = ['title', 'content']
    list_editable = ['is_published']
@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'action', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'detail']
    readonly_fields = ['user', 'action', 'detail', 'ip_address', 'created_at']