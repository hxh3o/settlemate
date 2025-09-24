from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import logging

from .models import Trip, ChatMessage, TripMember
from .serializers import ChatMessageSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_chat_message(request):
    """Add a chat message to a trip"""
    try:
        tripid = request.data.get('tripid')
        msg_data = request.data.get('msg')
        
        if not tripid or not msg_data:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID and message data are required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        
        # Check if user is a member of this trip
        if not TripMember.objects.filter(trip=trip, user=request.user, is_active=True).exists():
            return Response({
                'success': False,
                'errors': [{'msg': 'You are not a member of this trip'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create chat message
        chat_message = ChatMessage.objects.create(
            trip=trip,
            user=request.user,
            message=msg_data.get('msg', ''),
            is_image=msg_data.get('isImage', False),
            image_drive_id=msg_data.get('msg') if msg_data.get('isImage', False) else None
        )
        
        return Response({
            'success': True,
            'message': 'Message added successfully',
            'data': ChatMessageSerializer(chat_message).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Add chat message error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while adding message'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_chat(request):
    """Clear all chat messages for a trip (admin only)"""
    try:
        tripid = request.data.get('tripid')
        if not tripid:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        
        # Check if user is the trip owner
        if trip.owner != request.user:
            return Response({
                'success': False,
                'errors': [{'msg': 'Only trip owner can clear chat'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Clear all chat messages
        ChatMessage.objects.filter(trip=trip).delete()
        
        return Response({
            'success': True,
            'message': 'Chat cleared successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Clear chat error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while clearing chat'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_messages(request):
    """Get all chat messages for a trip"""
    try:
        tripid = request.GET.get('tripid')
        if not tripid:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        
        # Check if user is a member of this trip
        if not TripMember.objects.filter(trip=trip, user=request.user, is_active=True).exists():
            return Response({
                'success': False,
                'errors': [{'msg': 'You are not a member of this trip'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get chat messages
        messages = ChatMessage.objects.filter(trip=trip).select_related('user').order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get chat messages error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching chat messages'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
