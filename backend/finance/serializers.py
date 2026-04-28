from rest_framework import serializers

from users.serializers import PropertySerializer

from .models import Bill, ChargeItem, PaymentRecord


class ChargeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeItem
        fields = '__all__'


class PaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRecord
        fields = '__all__'
        read_only_fields = ['payment_time', 'operator']


class BillSerializer(serializers.ModelSerializer):
    property_detail = PropertySerializer(source='property', read_only=True)
    charge_item_name = serializers.CharField(source='charge_item.name', read_only=True)

    class Meta:
        model = Bill
        fields = '__all__'
