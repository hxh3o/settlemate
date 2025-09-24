from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, Trip, TripMember, Transaction, TransactionMember, 
    ChatMessage, TripInvite, PasswordResetToken, FileUpload
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'upi', 'profile_picture', 'is_verified', 'created_at']
        read_only_fields = ['id', 'is_verified', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        # Normalize and satisfy AbstractUser requirements
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        # Ensure username exists (AbstractUser expects it unless fully removed)
        email = validated_data.get('email', '').lower()
        validated_data['email'] = email
        validated_data.setdefault('username', email)
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])
    password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class TripSerializer(serializers.ModelSerializer):
    """Serializer for Trip model"""
    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = ['id', 'name', 'description', 'owner', 'member_count', 'is_active', 'created_at', 'updated_at', 'last_edited']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'last_edited']
    
    def get_member_count(self, obj):
        return obj.members.count()


class TripCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating trips"""
    class Meta:
        model = Trip
        fields = ['name', 'description']
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class TripMemberSerializer(serializers.ModelSerializer):
    """Serializer for TripMember model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TripMember
        fields = ['user', 'joined_at', 'is_active']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    paid_by = UserSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = ['id', 'name', 'description', 'amount', 'paid_by', 'bill_image', 'bill_drive_id', 'is_enabled', 'members', 'created_at', 'updated_at']
        read_only_fields = ['id', 'paid_by', 'created_at', 'updated_at']
    
    def get_members(self, obj):
        members = obj.members.all()
        return TransactionMemberSerializer(members, many=True).data


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions"""
    member_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        help_text="List of user IDs who should be included in this transaction"
    )
    
    class Meta:
        model = Transaction
        fields = ['name', 'description', 'amount', 'bill_image', 'bill_drive_id', 'member_ids']
    
    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids')
        validated_data['paid_by'] = self.context['request'].user
        transaction = super().create(validated_data)
        
        # Create TransactionMember instances
        for member_id in member_ids:
            try:
                user = User.objects.get(id=member_id)
                TransactionMember.objects.create(
                    transaction=transaction,
                    user=user,
                    amount_owed=transaction.amount / len(member_ids)
                )
            except User.DoesNotExist:
                pass
        
        return transaction


class TransactionMemberSerializer(serializers.ModelSerializer):
    """Serializer for TransactionMember model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TransactionMember
        fields = ['user', 'amount_owed', 'is_included']


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'message', 'is_image', 'image_drive_id', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TripInviteSerializer(serializers.ModelSerializer):
    """Serializer for TripInvite model"""
    invited_by = UserSerializer(read_only=True)
    invited_user = UserSerializer(read_only=True)
    
    class Meta:
        model = TripInvite
        fields = ['id', 'invited_by', 'invited_email', 'invited_user', 'status', 'created_at', 'expires_at']
        read_only_fields = ['id', 'invited_by', 'created_at', 'expires_at']


class TripInviteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating trip invites"""
    class Meta:
        model = TripInvite
        fields = ['invited_email']
    
    def create(self, validated_data):
        validated_data['invited_by'] = self.context['request'].user
        return super().create(validated_data)


class FileUploadSerializer(serializers.ModelSerializer):
    """Serializer for FileUpload model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = FileUpload
        fields = ['id', 'user', 'file_name', 'file_size', 'file_type', 'drive_file_id', 'drive_url', 'uploaded_at']
        read_only_fields = ['id', 'user', 'uploaded_at']


class TransferCalculationSerializer(serializers.Serializer):
    """Serializer for transfer calculation results"""
    from_user = UserSerializer()
    to_user = UserSerializer()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        fields = ['from_user', 'to_user', 'amount']
