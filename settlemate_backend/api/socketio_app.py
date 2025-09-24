import socketio
import logging
from django.conf import settings
from django.utils import timezone
from .models import Trip, ChatMessage, TripMember, User
from .authentication import verify_jwt_token

logger = logging.getLogger(__name__)

"""
Socket.IO server configured to run with 'eventlet' for proper WebSocket support.
Falls back to long-polling when websocket isn't available.
"""

# Create Socket.IO server (eventlet mode)
sio = socketio.Server(async_mode='eventlet',
    cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS,
    logger=True,
    engineio_logger=True
)

# Note: The WSGI app is mounted in app.py with Django's WSGI application.


@sio.event
def connect(sid, environ, auth=None):
    """Handle client connection. Do not force auth here; validate on actions."""
    try:
        if auth and 'token' in auth:
            user = verify_jwt_token(auth['token'])
            if user:
                sio.save_session(sid, {'user_id': str(user.id), 'user_email': user.email})
                logger.info(f"User {user.email} connected with session {sid}")
            else:
                logger.info(f"Anonymous client {sid} connected (invalid token)")
        else:
            logger.info(f"Anonymous client {sid} connected")
    except Exception as e:
        logger.error(f"Connect handler error: {str(e)}")


@sio.event
def disconnect(sid):
    """Handle client disconnection"""
    session = sio.get_session(sid)
    if session and 'user_email' in session:
        logger.info(f"User {session['user_email']} disconnected from session {sid}")
    else:
        logger.info(f"Client {sid} disconnected")


@sio.event
def join_room(sid, data):
    """Handle joining a trip room"""
    try:
        room_id = data.get('roomId')
        if not room_id:
            sio.emit('error', {'message': 'Room ID is required'}, room=sid)
            return
        
        session = sio.get_session(sid)
        if not session or 'user_id' not in session:
            sio.emit('error', {'message': 'Authentication required'}, room=sid)
            return
        
        # Verify user is member of the trip
        try:
            trip = Trip.objects.get(id=room_id, is_active=True)
            user = User.objects.get(id=session['user_id'])
            
            if not TripMember.objects.filter(trip=trip, user=user, is_active=True).exists():
                sio.emit('error', {'message': 'You are not a member of this trip'}, room=sid)
                return
            
            # Join the room
            sio.enter_room(sid, room_id)
            logger.info(f"User {user.email} joined room {room_id}")
            
            # Send confirmation
            sio.emit('joined_room', {'roomId': room_id}, room=sid)
            
        except (Trip.DoesNotExist, User.DoesNotExist):
            sio.emit('error', {'message': 'Invalid trip or user'}, room=sid)
            
    except Exception as e:
        logger.error(f"Join room error: {str(e)}")
        sio.emit('error', {'message': 'An error occurred while joining room'}, room=sid)


@sio.event
def leave_room(sid, data):
    """Handle leaving a trip room"""
    try:
        room_id = data.get('roomId')
        if not room_id:
            sio.emit('error', {'message': 'Room ID is required'}, room=sid)
            return
        
        sio.leave_room(sid, room_id)
        
        session = sio.get_session(sid)
        if session and 'user_email' in session:
            logger.info(f"User {session['user_email']} left room {room_id}")
        
        sio.emit('left_room', {'roomId': room_id}, room=sid)
        
    except Exception as e:
        logger.error(f"Leave room error: {str(e)}")
        sio.emit('error', {'message': 'An error occurred while leaving room'}, room=sid)


@sio.event
def msg(sid, data):
    """Handle chat message"""
    try:
        message_data = data.get('message')
        room_id = data.get('roomId')
        
        if not message_data or not room_id:
            sio.emit('error', {'message': 'Message data and room ID are required'}, room=sid)
            return
        
        session = sio.get_session(sid)
        if not session or 'user_id' not in session:
            sio.emit('error', {'message': 'Authentication required'}, room=sid)
            return
        
        # Verify user is member of the trip
        try:
            trip = Trip.objects.get(id=room_id, is_active=True)
            user = User.objects.get(id=session['user_id'])
            
            if not TripMember.objects.filter(trip=trip, user=user, is_active=True).exists():
                sio.emit('error', {'message': 'You are not a member of this trip'}, room=sid)
                return
            
            # Create chat message
            chat_message = ChatMessage.objects.create(
                trip=trip,
                user=user,
                message=message_data.get('msg', ''),
                is_image=message_data.get('isImage', False),
                image_drive_id=message_data.get('msg') if message_data.get('isImage', False) else None
            )
            
            # Prepare message for broadcast
            broadcast_message = {
                'from': str(user.id),
                'msg': message_data.get('msg', ''),
                'isImage': message_data.get('isImage', False),
                'date': chat_message.created_at.isoformat(),
                'user': {
                    'id': str(user.id),
                    'name': user.name,
                    'email': user.email
                }
            }
            
            # Broadcast to all users in the room
            sio.emit('bcast', broadcast_message, room=room_id)
            
            logger.info(f"Message from {user.email} broadcasted to room {room_id}")
            
        except (Trip.DoesNotExist, User.DoesNotExist):
            sio.emit('error', {'message': 'Invalid trip or user'}, room=sid)
            
    except Exception as e:
        logger.error(f"Message error: {str(e)}")
        sio.emit('error', {'message': 'An error occurred while sending message'}, room=sid)


@sio.event
def typing(sid, data):
    """Handle typing indicator"""
    try:
        room_id = data.get('roomId')
        is_typing = data.get('isTyping', False)
        
        if not room_id:
            sio.emit('error', {'message': 'Room ID is required'}, room=sid)
            return
        
        session = sio.get_session(sid)
        if not session or 'user_id' not in session:
            sio.emit('error', {'message': 'Authentication required'}, room=sid)
            return
        
        # Broadcast typing indicator to other users in the room
        typing_data = {
            'userId': session['user_id'],
            'isTyping': is_typing
        }
        
        sio.emit('user_typing', typing_data, room=room_id, skip_sid=sid)
        
    except Exception as e:
        logger.error(f"Typing error: {str(e)}")


@sio.event
def clear_chat(sid, data):
    """Handle chat clearing (admin only)"""
    try:
        room_id = data.get('roomId')
        
        if not room_id:
            sio.emit('error', {'message': 'Room ID is required'}, room=sid)
            return
        
        session = sio.get_session(sid)
        if not session or 'user_id' not in session:
            sio.emit('error', {'message': 'Authentication required'}, room=sid)
            return
        
        # Verify user is trip owner
        try:
            trip = Trip.objects.get(id=room_id, is_active=True)
            user = User.objects.get(id=session['user_id'])
            
            if trip.owner != user:
                sio.emit('error', {'message': 'Only trip owner can clear chat'}, room=sid)
                return
            
            # Clear chat messages
            ChatMessage.objects.filter(trip=trip).delete()
            
            # Broadcast clear message
            clear_message = {
                'from': str(user.id),
                'msg': 'Admin cleared the chat!',
                'isImage': False,
                'date': timezone.now().isoformat(),
                'user': {
                    'id': str(user.id),
                    'name': user.name,
                    'email': user.email
                }
            }
            
            sio.emit('bcast', clear_message, room=room_id)
            
            logger.info(f"Chat cleared by {user.email} in room {room_id}")
            
        except (Trip.DoesNotExist, User.DoesNotExist):
            sio.emit('error', {'message': 'Invalid trip or user'}, room=sid)
            
    except Exception as e:
        logger.error(f"Clear chat error: {str(e)}")
        sio.emit('error', {'message': 'An error occurred while clearing chat'}, room=sid)
