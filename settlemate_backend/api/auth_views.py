from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import uuid
import logging

from .models import User, PasswordResetToken, TripInvite
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer,
    TripInviteSerializer
)
from .authentication import generate_jwt_token, invalidate_user_sessions

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """User registration endpoint"""
    try:
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = generate_jwt_token(user)
            
            return Response({
                'success': True,
                'message': 'User created successfully',
                'authToken': token,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred during registration'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint"""
    try:
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = generate_jwt_token(user)
            
            return Response({
                'success': True,
                'message': 'Login successful',
                'authToken': token,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred during login'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Password reset request endpoint"""
    try:
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Create password reset token
                reset_token = PasswordResetToken.objects.create(
                    user=user,
                    token=str(uuid.uuid4())
                )
                
                # Send email (in production, you'd send actual email)
                reset_url = f"{settings.FRONTEND_URL}/reset/{reset_token.token}"
                
                # For development, log the reset URL
                logger.info(f"Password reset URL for {email}: {reset_url}")
                
                # In production, uncomment this:
                # send_mail(
                #     'Password Reset Request',
                #     f'Click the following link to reset your password: {reset_url}',
                #     settings.EMAIL_HOST_USER,
                #     [email],
                #     fail_silently=False,
                # )
                
                return Response({
                    'success': True,
                    'message': 'Password reset link sent to your email'
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'errors': [{'msg': 'User with this email does not exist'}]
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while processing your request'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def change_password(request):
    """Password reset confirmation endpoint"""
    try:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            
            try:
                reset_token = PasswordResetToken.objects.get(
                    token=token,
                    is_used=False,
                    expires_at__gt=timezone.now()
                )
                
                user = reset_token.user
                user.set_password(password)
                user.save()
                
                # Mark token as used
                reset_token.is_used = True
                reset_token.save()
                
                # Invalidate all user sessions
                invalidate_user_sessions(user)
                
                return Response({
                    'success': True,
                    'message': 'Password updated successfully'
                }, status=status.HTTP_200_OK)
                
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'success': False,
                    'errors': [{'msg': 'Invalid or expired reset token'}]
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while updating password'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """User logout endpoint"""
    try:
        # Invalidate current session
        invalidate_user_sessions(request.user)
        
        return Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred during logout'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_data(request):
    """Get current user data endpoint"""
    try:
        serializer = UserSerializer(request.user)
        
        # Check for pending invites
        invites_count = TripInvite.objects.filter(
            invited_email=request.user.email,
            status='pending'
        ).count()
        
        return Response({
            'success': True,
            'data': serializer.data,
            'invites': invites_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get user data error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching user data'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_profile(request):
    """Edit user profile endpoint"""
    try:
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Edit profile error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while updating profile'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
