from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import Trip, Transaction, ChatMessage

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample users
        users = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                email=f'user{i}@example.com',
                defaults={
                    'name': f'User {i}',
                    'username': f'user{i}',
                    'upi': f'user{i}@paytm'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
            self.stdout.write(f'Created user: {user.email}')
        
        # Create sample trip
        trip, created = Trip.objects.get_or_create(
            name='Sample Trip to Goa',
            defaults={
                'description': 'A fun trip to Goa with friends',
                'owner': users[0]
            }
        )
        
        if created:
            # Add members to trip
            from api.models import TripMember
            for user in users:
                TripMember.objects.get_or_create(trip=trip, user=user)
            
            # Create sample transactions
            transactions_data = [
                {
                    'name': 'Hotel Booking',
                    'description': 'Hotel room for 3 nights',
                    'amount': 15000,
                    'paid_by': users[0]
                },
                {
                    'name': 'Flight Tickets',
                    'description': 'Round trip flight tickets',
                    'amount': 25000,
                    'paid_by': users[1]
                },
                {
                    'name': 'Food & Drinks',
                    'description': 'Restaurant bills and drinks',
                    'amount': 8000,
                    'paid_by': users[2]
                },
                {
                    'name': 'Taxi & Transport',
                    'description': 'Local transport and taxi rides',
                    'amount': 5000,
                    'paid_by': users[3]
                }
            ]
            
            for trans_data in transactions_data:
                transaction = Transaction.objects.create(
                    trip=trip,
                    **trans_data
                )
                
                # Add all users to transaction
                from api.models import TransactionMember
                amount_per_person = transaction.amount / len(users)
                for user in users:
                    TransactionMember.objects.create(
                        transaction=transaction,
                        user=user,
                        amount_owed=amount_per_person
                    )
            
            # Create sample chat messages
            chat_messages = [
                {'user': users[0], 'message': 'Hey everyone! Excited for the trip!'},
                {'user': users[1], 'message': 'Me too! Can\'t wait to explore Goa'},
                {'user': users[2], 'message': 'I\'ve already started packing 😄'},
                {'user': users[3], 'message': 'Don\'t forget sunscreen!'},
                {'user': users[4], 'message': 'I\'ll bring the camera for photos'},
            ]
            
            for msg_data in chat_messages:
                ChatMessage.objects.create(
                    trip=trip,
                    **msg_data
                )
            
            self.stdout.write(f'Created trip: {trip.name}')
            self.stdout.write(f'Created {len(transactions_data)} transactions')
            self.stdout.write(f'Created {len(chat_messages)} chat messages')
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
