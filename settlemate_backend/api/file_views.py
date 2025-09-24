from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone
import os
import uuid
import logging

from .models import Trip, TripMember, FileUpload
from .serializers import FileUploadSerializer

logger = logging.getLogger(__name__)


def get_google_drive_service():
    """Get Google Drive service instance"""
    # This is a simplified version - in production, you'd need proper OAuth flow
    # For now, we'll return None and handle file uploads locally
    try:
        # Optional Google Drive imports
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        return None  # Return None for now
    except ImportError:
        logger.warning("Google Drive libraries not installed. Using local storage.")
        return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_files(request):
    """Upload files to Google Drive or local storage"""
    try:
        files = request.FILES.getlist('files')
        tripid = request.data.get('tripid')
        
        if not files:
            return Response({
                'success': False,
                'errors': [{'msg': 'No files provided'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_files = []
        
        for file in files:
            # Generate unique filename
            file_extension = os.path.splitext(file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Save file locally (in production, upload to Google Drive)
            file_path = default_storage.save(f"uploads/{unique_filename}", file)
            file_url = default_storage.url(file_path)
            
            # Create FileUpload record
            file_upload = FileUpload.objects.create(
                user=request.user,
                trip=Trip.objects.get(id=tripid) if tripid else None,
                file_name=file.name,
                file_size=file.size,
                file_type=file.content_type,
                drive_file_id=unique_filename,  # Using local filename as ID for now
                drive_url=file_url
            )
            
            uploaded_files.append(file_upload.drive_file_id)
        
        return Response({
            'success': True,
            'message': 'Files uploaded successfully',
            'files': uploaded_files
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Upload files error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while uploading files'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_file_info(request):
    """Get information about uploaded files"""
    try:
        file_id = request.GET.get('file_id')
        if not file_id:
            return Response({
                'success': False,
                'errors': [{'msg': 'File ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file_upload = get_object_or_404(FileUpload, drive_file_id=file_id)
        
        # Check if user has access to this file
        if file_upload.user != request.user:
            # Check if user is member of the trip this file belongs to
            if file_upload.trip:
                from .models import TripMember
                if not TripMember.objects.filter(
                    trip=file_upload.trip, 
                    user=request.user, 
                    is_active=True
                ).exists():
                    return Response({
                        'success': False,
                        'errors': [{'msg': 'You do not have access to this file'}]
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'success': False,
                    'errors': [{'msg': 'You do not have access to this file'}]
                }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = FileUploadSerializer(file_upload)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get file info error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching file info'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trip_files(request):
    """Get all files uploaded to a trip"""
    try:
        tripid = request.GET.get('tripid')
        if not tripid:
            return Response({
                'success': False,
                'errors': [{'msg': 'Trip ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        trip = get_object_or_404(Trip, id=tripid, is_active=True)
        
        # Check if user is a member of this trip
        from .models import TripMember
        if not TripMember.objects.filter(trip=trip, user=request.user, is_active=True).exists():
            return Response({
                'success': False,
                'errors': [{'msg': 'You are not a member of this trip'}]
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get files for this trip
        files = FileUpload.objects.filter(trip=trip).order_by('-uploaded_at')
        serializer = FileUploadSerializer(files, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Get trip files error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while fetching files'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request):
    """Delete an uploaded file"""
    try:
        file_id = request.data.get('file_id')
        if not file_id:
            return Response({
                'success': False,
                'errors': [{'msg': 'File ID is required'}]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file_upload = get_object_or_404(FileUpload, drive_file_id=file_id)
        
        # Check if user is the uploader or trip owner
        if file_upload.user != request.user:
            if file_upload.trip and file_upload.trip.owner != request.user:
                return Response({
                    'success': False,
                    'errors': [{'msg': 'You are not authorized to delete this file'}]
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Delete file from storage
        try:
            default_storage.delete(f"uploads/{file_upload.drive_file_id}")
        except Exception as e:
            logger.warning(f"Could not delete file from storage: {str(e)}")
        
        # Delete database record
        file_upload.delete()
        
        return Response({
            'success': True,
            'message': 'File deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Delete file error: {str(e)}")
        return Response({
            'success': False,
            'errors': [{'msg': 'An error occurred while deleting file'}]
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
