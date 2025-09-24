import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import authentication, exceptions
from rest_framework.authentication import BaseAuthentication
from .models import User, UserSession


class JWTAuthentication(BaseAuthentication):
    """Custom JWT Authentication for Django REST Framework"""
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
            
        try:
            token = auth_header.split(' ')[1]  # Remove 'Bearer ' prefix
        except IndexError:
            return None
            
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')
            
        try:
            user = User.objects.get(id=payload['user_id'])
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
            
        # Check if session is still active
        try:
            session = UserSession.objects.get(
                token=token,
                user=user,
                is_active=True,
                expires_at__gt=datetime.now()
            )
        except UserSession.DoesNotExist:
            raise exceptions.AuthenticationFailed('Session expired')
            
        return (user, token)
    
    def authenticate_header(self, request):
        return 'Bearer'


def generate_jwt_token(user):
    """Generate JWT token for user"""
    payload = {
        'user_id': str(user.id),
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION_DELTA),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    # Create or update user session
    expires_at = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION_DELTA)
    UserSession.objects.update_or_create(
        user=user,
        defaults={
            'token': token,
            'expires_at': expires_at,
            'is_active': True
        }
    )
    
    return token


def verify_jwt_token(token):
    """Verify JWT token and return user"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user = User.objects.get(id=payload['user_id'])
        
        # Check if session is still active
        session = UserSession.objects.get(
            token=token,
            user=user,
            is_active=True,
            expires_at__gt=datetime.now()
        )
        
        return user
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, User.DoesNotExist, UserSession.DoesNotExist):
        return None


def invalidate_user_sessions(user):
    """Invalidate all sessions for a user"""
    UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
