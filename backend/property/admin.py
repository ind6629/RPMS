from django.contrib import admin
from .models import RepairOrder, Complaint, ServiceFeedback
@admin.register(RepairOrder)
class RepairOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'property', 'user', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['description', 'property__name', 'user__username']
    date_hierarchy = 'created_at'
    raw_id_fields = ['property', 'user', 'assigned_to']
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'title', 'status', 'handler', 'created_at']
    list_filter = ['type', 'status', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user', 'handler']
@admin.register(ServiceFeedback)
class ServiceFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'rating', 'comment', 'created_at']
    list_filter = ['rating', 'created_at']
    raw_id_fields = ['order']