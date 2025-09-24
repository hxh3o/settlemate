from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import auth_views, trip_views, transaction_views, chat_views

urlpatterns = [
    # Authentication endpoints
    path('signup', auth_views.signup, name='signup'),
    path('login', auth_views.login, name='login'),
    path('logout', auth_views.logout, name='logout'),
    path('forgotPassword', auth_views.forgot_password, name='forgot_password'),
    path('changePassword', auth_views.change_password, name='change_password'),
    path('getUserData', auth_views.get_user_data, name='get_user_data'),
    path('editprofile', auth_views.edit_profile, name='edit_profile'),
    
    # Trip management endpoints
    path('createtrip', trip_views.create_trip, name='create_trip'),
    path('getTripsData', trip_views.get_trips_data, name='get_trips_data'),
    path('getTripData', trip_views.get_trip_data, name='get_trip_data'),
    path('getTripMembers', trip_views.get_trip_members, name='get_trip_members'),
    path('kickMember', trip_views.kick_member, name='kick_member'),
    path('adminMember', trip_views.admin_member, name='admin_member'),
    path('invite', trip_views.invite_member, name='invite_member'),
    path('acceptInvite', trip_views.accept_invite, name='accept_invite'),
    path('declineInvite', trip_views.decline_invite, name='decline_invite'),
    path('getInvites', trip_views.get_invites, name='get_invites'),
    path('edittrip', trip_views.edit_trip, name='edit_trip'),
    
    # Transaction management endpoints
    path('createtransaction', transaction_views.create_transaction, name='create_transaction'),
    path('getTransactions', transaction_views.get_transactions, name='get_transactions'),
    path('getTransactionData', transaction_views.get_transaction_data, name='get_transaction_data'),
    path('edittransaction', transaction_views.edit_transaction, name='edit_transaction'),
    path('deleteTransaction', transaction_views.delete_transaction, name='delete_transaction'),
    path('calculateTransfers', transaction_views.calculate_transfers, name='calculate_transfers'),
    path('getTripTransfers', transaction_views.calculate_transfers, name='get_trip_transfers'),
    
    # Chat endpoints
    path('addChat', chat_views.add_chat_message, name='add_chat_message'),
    path('clearChat', chat_views.clear_chat, name='clear_chat'),
    path('getChatMessages', chat_views.get_chat_messages, name='get_chat_messages'),
    
    # Removed file upload endpoints
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
