from django.contrib import admin
from .models import User, UserProfile, Property

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'role', 'phone', 'status', 'created_at']
    list_filter = ['role', 'status']
    search_fields = ['username', 'phone']
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'gender', 'id_card', 'address']
    search_fields = ['user__username', 'id_card']
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'property_type', 'building_number', 'unit_number', 'room_number', 'owner', 'status']
    list_filter = ['property_type', 'status']
    search_fields = ['building_number', 'unit_number', 'room_number', 'name']