from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Trip, TripMember, Transaction, TransactionMember,
    ChatMessage, TripInvite, PasswordResetToken, UserSession, FileUpload
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model"""
    list_display = ['email', 'name', 'is_verified', 'is_active', 'created_at']
    list_filter = ['is_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'name']
    ordering = ['-created_at']
    # Non-editable timestamp fields must be read-only in admin forms
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'upi', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """Admin configuration for Trip model"""
    list_display = ['name', 'owner', 'member_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'owner__name', 'owner__email']
    ordering = ['-created_at']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(TripMember)
class TripMemberAdmin(admin.ModelAdmin):
    """Admin configuration for TripMember model"""
    list_display = ['trip', 'user', 'is_active', 'joined_at']
    list_filter = ['is_active', 'joined_at']
    search_fields = ['trip__name', 'user__name', 'user__email']
    ordering = ['-joined_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model"""
    list_display = ['name', 'trip', 'amount', 'paid_by', 'is_enabled', 'created_at']
    list_filter = ['is_enabled', 'created_at']
    search_fields = ['name', 'trip__name', 'paid_by__name']
    ordering = ['-created_at']


@admin.register(TransactionMember)
class TransactionMemberAdmin(admin.ModelAdmin):
    """Admin configuration for TransactionMember model"""
    list_display = ['transaction', 'user', 'amount_owed', 'is_included']
    list_filter = ['is_included']
    search_fields = ['transaction__name', 'user__name', 'user__email']
    ordering = ['-transaction__created_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin configuration for ChatMessage model"""
    list_display = ['trip', 'user', 'message_preview', 'is_image', 'created_at']
    list_filter = ['is_image', 'created_at']
    search_fields = ['trip__name', 'user__name', 'message']
    ordering = ['-created_at']
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'


@admin.register(TripInvite)
class TripInviteAdmin(admin.ModelAdmin):
    """Admin configuration for TripInvite model"""
    list_display = ['trip', 'invited_email', 'invited_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['trip__name', 'invited_email', 'invited_by__name']
    ordering = ['-created_at']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin configuration for PasswordResetToken model"""
    list_display = ['user', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'user__name']
    ordering = ['-created_at']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin configuration for UserSession model"""
    list_display = ['user', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'user__name']
    ordering = ['-created_at']


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    """Admin configuration for FileUpload model"""
    list_display = ['file_name', 'user', 'trip', 'file_size', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['file_name', 'user__name', 'trip__name']
    ordering = ['-uploaded_at']