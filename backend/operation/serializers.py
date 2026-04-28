from rest_framework import serializers

from .models import Announcement, SystemLog


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = '__all__'


class SystemLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True, allow_null=True)

    class Meta:
        model = SystemLog
        fields = ['id', 'user', 'user_name', 'action', 'detail', 'ip_address', 'created_at']
        read_only_fields = ['id', 'user', 'user_name', 'action', 'detail', 'ip_address', 'created_at']
