from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settlemate.settings')

app = Celery('settlemate')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Email tasks
@app.task
def send_password_reset_email(email, reset_url):
    """Send password reset email"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = 'Password Reset Request - SettleMate'
    message = f'''
    You have requested to reset your password for SettleMate.
    
    Click the following link to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you did not request this password reset, please ignore this email.
    
    Best regards,
    SettleMate Team
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return f"Password reset email sent to {email}"
    except Exception as e:
        return f"Failed to send email to {email}: {str(e)}"


@app.task
def send_trip_invite_email(email, trip_name, invite_url):
    """Send trip invitation email"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = f'Invitation to join {trip_name} - SettleMate'
    message = f'''
    You have been invited to join the trip "{trip_name}" on SettleMate.
    
    Click the following link to accept the invitation:
    {invite_url}
    
    This invitation will expire in 7 days.
    
    If you do not want to join this trip, you can simply ignore this email.
    
    Best regards,
    SettleMate Team
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return f"Trip invite email sent to {email}"
    except Exception as e:
        return f"Failed to send email to {email}: {str(e)}"


@app.task
def cleanup_expired_tokens():
    """Clean up expired password reset tokens"""
    from .models import PasswordResetToken
    from django.utils import timezone
    
    expired_tokens = PasswordResetToken.objects.filter(
        expires_at__lt=timezone.now()
    )
    
    count = expired_tokens.count()
    expired_tokens.delete()
    
    return f"Cleaned up {count} expired tokens"


@app.task
def cleanup_expired_sessions():
    """Clean up expired user sessions"""
    from .models import UserSession
    from django.utils import timezone
    
    expired_sessions = UserSession.objects.filter(
        expires_at__lt=timezone.now()
    )
    
    count = expired_sessions.count()
    expired_sessions.update(is_active=False)
    
    return f"Cleaned up {count} expired sessions"
