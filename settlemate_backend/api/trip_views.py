from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

from .models import Trip, TripMember, TripInvite, User, ChatMessage
from .serializers import (
    TripSerializer, TripCreateSerializer, TripMemberSerializer,
    TripInviteSerializer, TripInviteCreateSerializer, ChatMessageSerializer
)
from .authentication import generate_jwt_token
from uuid import UUID

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_trip(request):
    """Create a new trip"""
    try:
        serializer = TripCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            trip = serializer.save()
            
            # Add creator as a member
            TripMember.objects.create(trip=trip, user=request.user)
            
            return Response({
                'success': True,
                'message': 'Trip created successfully',
                'tripid': str(trip.id)
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Create trip error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while creating the trip'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trips_data(request):
    """Get all trips for the current user"""
    try:
        # Get trips where user is a member
        trips = Trip.objects.filter(
            members=request.user,
            is_active=True
        ).select_related('owner').prefetch_related('members')
        
        serializer = TripSerializer(trips, many=True)
        
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
        logger.error(f"Get trips data error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching trips'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_trip_members(request):
    try:
        tripid = request.data.get('tripid')
        if not tripid:
            return Response({'success': False, 'errors': [{'msg': 'Trip ID is required'}]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            UUID(str(tripid))
        except Exception:
            return Response({'success': False, 'errors': [{'msg': 'Invalid trip ID'}]}, status=status.HTTP_400_BAD_REQUEST)

        trip = get_object_or_404(Trip, id=tripid, is_active=True)

        # Must be a member
        if not TripMember.objects.filter(trip=trip, user=request.user, is_active=True).exists():
            return Response({'success': False, 'errors': [{'msg': 'You are not a member of this trip'}]}, status=status.HTTP_403_FORBIDDEN)

        members = TripMember.objects.filter(trip=trip, is_active=True).select_related('user')
        members_list = [{'_id': str(m.user.id), 'name': m.user.name, 'email': m.user.email} for m in members]

        return Response({'success': True, 'data': {'members': members_list}, 'myID': str(request.user.id)}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Get trip members error: {str(e)}")
        return Response({'success': False, 'errors': [{'msg': 'An error occurred while fetching members'}]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def kick_member(request):
    try:
        tripid = request.data.get('tripid')
        userid = request.data.get('userid')
        if not tripid or not userid:
            return Response({'success': False, 'errors': [{'msg': 'Trip ID and User ID are required'}]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            UUID(str(tripid)); UUID(str(userid))
        except Exception:
            return Response({'success': False, 'errors': [{'msg': 'Invalid IDs'}]}, status=status.HTTP_400_BAD_REQUEST)

        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        if trip.owner != request.user:
            return Response({'success': False, 'errors': [{'msg': 'Only trip owner can kick members'}]}, status=status.HTTP_403_FORBIDDEN)

        member = get_object_or_404(TripMember, trip=trip, user_id=userid, is_active=True)
        if str(trip.owner.id) == str(userid):
            return Response({'success': False, 'errors': [{'msg': 'Owner cannot be removed'}]}, status=status.HTTP_400_BAD_REQUEST)

        member.is_active = False
        member.save()
        return Response({'success': True, 'message': 'Member removed'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Kick member error: {str(e)}")
        return Response({'success': False, 'errors': [{'msg': 'An error occurred while removing member'}]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_member(request):
    try:
        tripid = request.data.get('tripid')
        userid = request.data.get('userid')
        if not tripid or not userid:
            return Response({'success': False, 'errors': [{'msg': 'Trip ID and User ID are required'}]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            UUID(str(tripid)); UUID(str(userid))
        except Exception:
            return Response({'success': False, 'errors': [{'msg': 'Invalid IDs'}]}, status=status.HTTP_400_BAD_REQUEST)

        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        if trip.owner != request.user:
            return Response({'success': False, 'errors': [{'msg': 'Only current owner can transfer ownership'}]}, status=status.HTTP_403_FORBIDDEN)

        new_owner = get_object_or_404(TripMember, trip=trip, user_id=userid, is_active=True).user
        trip.owner = new_owner
        trip.save()
        return Response({'success': True, 'message': 'Ownership transferred'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Admin member error: {str(e)}")
        return Response({'success': False, 'errors': [{'msg': 'An error occurred while transferring ownership'}]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_trip_data(request):
    """Get detailed data for a specific trip"""
    try:
        tripid = request.data.get('tripid')
        if not tripid:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            UUID(str(tripid))
        except Exception:
            return Response({'success': False, 'errors': [{'msg': 'Invalid trip ID'}]}, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        
        # Check if user is a member of this trip
        if not TripMember.objects.filter(trip=trip, user=request.user, is_active=True).exists():
            return Response({
                'success': False,
                'errors': [{'msg': 'You are not a member of this trip'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get trip data
        trip_data = TripSerializer(trip).data
        
        # Get members
        members = TripMember.objects.filter(trip=trip, is_active=True).select_related('user')
        members_data = [{'name': m.user.name, 'email': m.user.email, '_id': str(m.user.id)} for m in members]
        
        # Get chat messages and normalize to frontend shape
        chat_messages = ChatMessage.objects.filter(trip=trip).select_related('user').order_by('created_at')
        serialized = ChatMessageSerializer(chat_messages, many=True).data
        chat_data = [
            {
                'from': str(cm['user']['id']) if isinstance(cm.get('user'), dict) and cm['user'].get('id') else str(cm.get('user', '')),
                'msg': cm.get('message', ''),
                'isImage': cm.get('is_image', False),
                'date': cm.get('created_at'),
            }
            for cm in serialized
        ]
        
        # Create user ID to name mapping
        map_id2name = {m['_id']: m['name'] for m in members_data}
        
        return Response({
            'success': True,
            'data': trip_data,
            'members': members_data,
            'chat': chat_data,
            'mapId2Name': map_id2name,
            'userId': str(request.user.id)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get trip data error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching trip data'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invite_member(request):
    """Invite a member to a trip"""
    try:
        tripid = request.data.get('tripid')
        email = request.data.get('email')
        
        if not tripid or not email:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID and email are required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        
        # Check if user is the owner
        if trip.owner != request.user:
            return Response({
                'success': False,
                'errors': [{'msg': 'Only trip owner can invite members'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user is already a member
        if TripMember.objects.filter(trip=trip, user__email=email, is_active=True).exists():
            return Response({
                'success': False,
                'errors': [{'msg': 'User is already a member of this trip'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if there's already a pending invite
        if TripInvite.objects.filter(trip=trip, invited_email=email, status='pending').exists():
            return Response({
                'success': False,
                'errors': [{'msg': 'Invite already sent to this email'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create invite
        invite = TripInvite.objects.create(
            trip=trip,
            invited_by=request.user,
            invited_email=email
        )
        
        # Try to find existing user
        try:
            invited_user = User.objects.get(email=email)
            invite.invited_user = invited_user
            invite.save()
        except User.DoesNotExist:
            pass
        
        # Send email notification (in production)
        invite_url = f"{settings.FRONTEND_URL}/invite/{invite.id}"
        
        # For development, log the invite URL
        logger.info(f"Trip invite URL for {email}: {invite_url}")
        
        # In production, uncomment this:
        # send_mail(
        #     f'Invitation to join {trip.name}',
        #     f'You have been invited to join the trip "{trip.name}". Click here to accept: {invite_url}',
        #     settings.EMAIL_HOST_USER,
        #     [email],
        #     fail_silently=False,
        # )
        
        return Response({
            'success': True,
            'message': f'Invite sent to {email}'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Invite member error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while sending invite'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invite(request):
    """Accept a trip invitation"""
    try:
        invite_id = request.data.get('invite_id')
        if not invite_id:
            return Response({
                'success': False,
                'errors': [{'msg': 'Invite ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        invite = get_object_or_404(TripInvite, id=invite_id)
        
        # Check if invite is for current user
        if invite.invited_email != request.user.email:
            return Response({
                'success': False,
                'errors': [{'msg': 'This invite is not for you'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if invite is still valid
        if invite.status != 'pending' or invite.expires_at < timezone.now():
            return Response({
                'success': False,
                'errors': [{'msg': 'Invite has expired or is no longer valid'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add user to trip
        with transaction.atomic():
            TripMember.objects.create(trip=invite.trip, user=request.user)
            invite.status = 'accepted'
            invite.invited_user = request.user
            invite.save()
        
        return Response({
            'success': True,
            'message': f'Successfully joined {invite.trip.name}',
            'tripid': str(invite.trip.id)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Accept invite error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while accepting invite'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_invite(request):
    """Decline a trip invitation"""
    try:
        invite_id = request.data.get('invite_id')
        if not invite_id:
            return Response({
                'success': False,
                'errors': [{'msg': 'Invite ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        invite = get_object_or_404(TripInvite, id=invite_id)
        
        # Check if invite is for current user
        if invite.invited_email != request.user.email:
            return Response({
                'success': False,
                'errors': [{'msg': 'This invite is not for you'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if invite is still valid
        if invite.status != 'pending':
            return Response({
                'success': False,
                'errors': [{'msg': 'Invite is no longer valid'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Decline invite
        invite.status = 'declined'
        invite.save()
        
        return Response({
            'success': True,
            'message': 'Invite declined'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Decline invite error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while declining invite'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invites(request):
    """Get all invites for the current user"""
    try:
        invites = TripInvite.objects.filter(
            invited_email=request.user.email,
            status='pending'
        ).select_related('trip', 'invited_by')
        
        # Shape invites for frontend: include trip info and stable ids
        data = [
            {
                '_id': str(invite.id),
                'name': invite.trip.name,
                'owner': {
                    'name': invite.trip.owner.name,
                    'email': invite.trip.owner.email,
                },
                'tripid': str(invite.trip.id),
                'status': invite.status,
                'created_at': invite.created_at,
                'expires_at': invite.expires_at,
            }
            for invite in invites
        ]
        
        return Response({
            'success': True,
            'data': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get invites error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching invites'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_trip(request):
    """Edit trip details"""
    try:
        tripid = request.data.get('tripid')
        if not tripid:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        
        # Check if user is the owner
        if trip.owner != request.user:
            return Response({
                'success': False,
                'errors': [{'msg': 'Only trip owner can edit trip details'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TripSerializer(trip, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'success': True,
                'message': 'Trip updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Edit trip error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while updating trip'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
