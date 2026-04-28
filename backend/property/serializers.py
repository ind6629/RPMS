from rest_framework import serializers
from .models import RepairOrder, Complaint, ServiceFeedback
from users.serializers import PropertySerializer, UserSerializer


class RepairOrderSerializer(serializers.ModelSerializer):
    property_detail = PropertySerializer(source='property', read_only=True)
    user_info = UserSerializer(source='user', read_only=True)
    assigned_to_info = UserSerializer(source='assigned_to', read_only=True)
    
    class Meta:
        model = RepairOrder
        fields = [
            'id', 'property', 'property_detail', 'user', 'user_info', 
            'description', 'images', 'status', 'assigned_to', 'assigned_to_info',
            'assigned_at', 'completed_at', 'remark', 'created_at', 'updated_at'
        ]


class RepairOrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairOrder
        fields = ['property', 'description', 'images']

    def validate_property(self, value):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and getattr(user, 'role', None) == 'owner':
            if value.owner_id != user.id:
                raise serializers.ValidationError('只能选择您名下的房产')
        return value


class ComplaintSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source='user', read_only=True)
    handler_info = UserSerializer(source='handler', read_only=True)
    
    class Meta:
        model = Complaint
        fields= [
            'id', 'user', 'user_info', 'type', 'title', 'description', 
            'images', 'status', 'handler', 'handler_info', 'handler_remark',
            'completed_at', 'created_at', 'updated_at'
        ]


class ComplaintCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['type', 'title', 'description', 'images']


class ServiceFeedbackSerializer(serializers.ModelSerializer):
    order_detail = RepairOrderSerializer(source='order', read_only=True)
    
    class Meta:
        model = ServiceFeedback
        fields = ['id', 'order', 'order_detail', 'rating', 'comment', 'created_at']


class ServiceFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFeedback
        fields = ['order', 'rating', 'comment']

    def validate_order(self, order):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or order.user_id != user.id:
            raise serializers.ValidationError('仅报修人可评价')
        if order.status != 'completed':
            raise serializers.ValidationError('工单需已完成')
        if ServiceFeedback.objects.filter(order=order).exists():
            raise serializers.ValidationError('该工单已评价')
        return order