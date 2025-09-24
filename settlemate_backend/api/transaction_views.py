from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import logging

from .models import Trip, Transaction, TransactionMember, User, TripMember
from .serializers import (
    TransactionSerializer, TransactionCreateSerializer, 
    TransactionMemberSerializer
)
from .utils import calculate_minimum_transfers

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_transaction(request):
    """Create a new transaction"""
    try:
        tripid = request.data.get('tripid')
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
        
        # Provide sensible defaults when optional fields are omitted by client
        incoming = request.data.copy()
        # Normalize and validate amount
        try:
            incoming['amount'] = float(incoming.get('amount', 0))
        except Exception:
            return Response({
                'success': False,
                'errors': [{'msg': 'Amount must be a number'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        if incoming['amount'] < 0:
            return Response({
                'success': False,
                'errors': [{'msg': 'Amount cannot be negative'}]
            }, status=status.HTTP_400_BAD_REQUEST)

        # Ensure members: default to current user, and ensure they belong to trip
        member_ids = incoming.get('member_ids') or [str(request.user.id)]
        if not isinstance(member_ids, list):
            return Response({
                'success': False,
                'errors': [{'msg': 'member_ids must be an array of user IDs'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate membership
        valid_member_ids = []
        for uid in member_ids:
            try:
                user = User.objects.get(id=uid)
                if TripMember.objects.filter(trip=trip, user=user, is_active=True).exists():
                    valid_member_ids.append(str(user.id))
            except User.DoesNotExist:
                continue
        if not valid_member_ids:
            return Response({
                'success': False,
                'errors': [{'msg': 'No valid members provided for this trip'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        incoming['member_ids'] = valid_member_ids

        serializer = TransactionCreateSerializer(data=incoming, context={'request': request})
        if serializer.is_valid():
            with transaction.atomic():
                # Create transaction with required foreign keys
                transaction_obj = serializer.save(trip=trip)
                
                return Response({
                    'success': True,
                    'message': 'Transaction created successfully',
                    'transactionid': str(transaction_obj.id)
                }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Create transaction error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while creating the transaction'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transactions(request):
    """Get all transactions for a trip"""
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
        
        transactions = Transaction.objects.filter(
            trip=trip,
            is_enabled=True
        ).select_related('paid_by').prefetch_related('members__user').order_by('-created_at')
        
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get transactions error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching transactions'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_transaction_data(request):
    """Get detailed data for a specific transaction"""
    try:
        tripid = request.data.get('tripid')
        transactionid = request.data.get('transactionid')
        
        if not tripid or not transactionid:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID and Transaction ID are required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        transaction_obj = get_object_or_404(Transaction, id=transactionid, trip=trip)
        
        # Check if user is a member of this trip
        if not TripMember.objects.filter(trip=trip, user=request.user, is_active=True).exists():
            return Response({
                'success': False,
                'errors': [{'msg': 'You are not a member of this trip'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get transaction data
        transaction_data = TransactionSerializer(transaction_obj).data
        
        # Get members and their amounts
        members = TransactionMember.objects.filter(
            transaction=transaction_obj,
            is_included=True
        ).select_related('user')
        
        members_data = []
        amount_distribution = {}
        
        for member in members:
            members_data.append(member.user.id)
            amount_distribution[str(member.user.id)] = float(member.amount_owed)
        
        # Get member mapping
        member_mapping = {str(member.user.id): {
            'name': member.user.name,
            'email': member.user.email
        } for member in members}
        
        return Response({
            'success': True,
            'name': transaction_obj.name,
            'desc': transaction_obj.description,
            'amt': float(transaction_obj.amount),
            'bill': transaction_obj.bill_drive_id or '',
            'damg': members_data,
            'memmap': member_mapping,
            'damgmap': amount_distribution,
            'owner': {
                'name': transaction_obj.paid_by.name,
                'email': transaction_obj.paid_by.email,
                '_id': str(transaction_obj.paid_by.id)
            },
            'switchVal': transaction_obj.is_enabled,
            'myId': str(request.user.id),
            'tripOwner': str(trip.owner.id)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get transaction data error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching transaction data'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def edit_transaction(request):
    """Edit transaction details"""
    try:
        tripid = request.data.get('tripid')
        transactionid = request.data.get('transactionid')
        
        if not tripid or not transactionid:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID and Transaction ID are required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        transaction_obj = get_object_or_404(Transaction, id=transactionid, trip=trip)
        
        # Check if user is the transaction creator or trip owner
        if transaction_obj.paid_by != request.user and trip.owner != request.user:
            return Response({
                'success': False,
                'errors': [{'msg': 'You are not authorized to edit this transaction'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TransactionSerializer(transaction_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            return Response({
                'success': True,
                'message': 'Transaction updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': [{'msg': str(error)} for field, errors in serializer.errors.items() for error in errors]
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Edit transaction error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while updating transaction'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_transfers(request):
    """Calculate minimum transfers for a trip"""
    try:
        tripid = request.data.get('tripid')
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
        
        # Calculate transfers
        transfers = calculate_minimum_transfers(trip)
        
        return Response({
            'success': True,
            'data': transfers
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Calculate transfers error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while calculating transfers'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_transaction(request):
    """Delete a transaction"""
    try:
        tripid = request.data.get('tripid')
        transactionid = request.data.get('transactionid')
        
        if not tripid or not transactionid:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID and Transaction ID are required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        transaction_obj = get_object_or_404(Transaction, id=transactionid, trip=trip)
        
        # Check if user is the transaction creator or trip owner
        if transaction_obj.paid_by != request.user and trip.owner != request.user:
            return Response({
                'success': False,
                'errors': [{'msg': 'You are not authorized to delete this transaction'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Soft delete by disabling
        transaction_obj.is_enabled = False
        transaction_obj.save()
        
        return Response({
            'success': True,
            'message': 'Transaction deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Delete transaction error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while deleting transaction'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
