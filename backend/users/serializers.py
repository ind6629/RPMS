from rest_framework import serializers
from .models import User, UserProfile, Property


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ['user']


class PropertySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Property
        fields = ['id', 'name', 'property_type', 'parent', 'parent_name', 'building_number', 
                  'unit_number', 'room_number', 'area', 'owner', 'owner_name', 'status', 
                  'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    properties = PropertySerializer(many=True, read_only=True)
    properties_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone', 'avatar', 'status',
                  'is_superuser', 'created_at', 'updated_at', 'profile', 'properties', 'properties_count']
        extra_kwargs = {'password': {'write_only': True}}
    
    def get_properties_count(self, obj):
        return obj.properties.count()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    profile_data = serializers.DictField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'role', 'phone', 'profile_data']
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile_data', {})
        user = User.objects.create_user(**validated_data)
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False, partial=True)

    class Meta:
        model = User
        fields = ['email', 'phone', 'avatar', 'status', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data is not None:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class SelfProfileSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False, partial=True)

    class Meta:
        model = User
        fields = ['email', 'phone', 'avatar', 'profile']


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('原密码错误')
        return value