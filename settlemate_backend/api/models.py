from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    upi = models.CharField(max_length=50, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    def __str__(self):
        return f"{self.name} ({self.email})"


class Trip(models.Model):
    """Trip model for managing group trips"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_trips')
    members = models.ManyToManyField(User, through='TripMember', related_name='trips')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_edited = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (Owner: {self.owner.name})"


class TripMember(models.Model):
    """Through model for Trip-Member relationship"""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['trip', 'user']

    def __str__(self):
        return f"{self.user.name} in {self.trip.name}"


class Transaction(models.Model):
    """Transaction model for managing expenses"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='transactions')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paid_transactions')
    bill_image = models.ImageField(upload_to='bills/', blank=True, null=True)
    bill_drive_id = models.CharField(max_length=200, blank=True, null=True)  # Google Drive file ID
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - ₹{self.amount}"


class TransactionMember(models.Model):
    """Through model for Transaction-Member relationship"""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_included = models.BooleanField(default=True)

    class Meta:
        unique_together = ['transaction', 'user']

    def __str__(self):
        return f"{self.user.name} owes ₹{self.amount_owed} in {self.transaction.name}"


class ChatMessage(models.Model):
    """Chat message model for trip chat"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='chat_messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    is_image = models.BooleanField(default=False)
    image_drive_id = models.CharField(max_length=200, blank=True, null=True)  # Google Drive file ID
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.name}: {self.message[:50]}..."


class TripInvite(models.Model):
    """Trip invitation model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='invites')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    invited_email = models.EmailField()
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invites', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = ['trip', 'invited_email']

    def __str__(self):
        return f"Invite for {self.invited_email} to {self.trip.name}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)


class PasswordResetToken(models.Model):
    """Password reset token model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reset token for {self.user.email}"


class UserSession(models.Model):
    """User session model for JWT token management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=500, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    device_info = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session for {self.user.email}"


class FileUpload(models.Model):
    """File upload model for managing uploaded files"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='uploaded_files', blank=True, null=True)
    file_name = models.CharField(max_length=200)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=100)
    drive_file_id = models.CharField(max_length=200, unique=True)
    drive_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} uploaded by {self.user.name}"