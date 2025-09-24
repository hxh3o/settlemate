from decimal import Decimal
from collections import defaultdict
from typing import List, Dict, Tuple
from .models import Trip, Transaction, TransactionMember, User
from decimal import Decimal

def calculate_minimum_transfers(trip: Trip):
    # Build net balance per user
    balances = {}
    members = trip.members.filter(tripmember__is_active=True)
    for user in members:
        balances[str(user.id)] = Decimal('0')

    transactions = Transaction.objects.filter(trip=trip, is_enabled=True).prefetch_related('members__user')
    for t in transactions:
        paid_by_id = str(t.paid_by.id)
        balances[paid_by_id] = balances.get(paid_by_id, Decimal('0')) + Decimal(t.amount)
        included = list(TransactionMember.objects.filter(transaction=t, is_included=True))
        if included:
            share = Decimal(t.amount) / Decimal(len(included))
            for tm in included:
                uid = str(tm.user.id)
                balances[uid] = balances.get(uid, Decimal('0')) - share

    # Separate creditors and debtors
    debtors = []  # (user_id, amount_positive)
    creditors = []
    for uid, bal in balances.items():
        if bal < 0:
            debtors.append([uid, -bal])
        elif bal > 0:
            creditors.append([uid, bal])

    # Greedy settlement
    result = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        d_uid, d_amt = debtors[i]
        c_uid, c_amt = creditors[j]
        pay = min(d_amt, c_amt)
        result.append({
            'from': d_uid,
            'to': c_uid,
            'amount': float(round(pay, 2)),
        })
        debtors[i][1] -= pay
        creditors[j][1] -= pay
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    # Map IDs to user info
    users = {str(u.id): u for u in members}
    transfers = []
    for item in result:
        from_u = users[item['from']]
        to_u = users[item['to']]
        transfers.append({
            'amt': float(item['amount']),
            'from': {
                'name': from_u.name,
                'email': from_u.email,
            },
            'to': {
                'name': to_u.name,
                'email': to_u.email,
                'upi': to_u.upi or '',
            }
        })

    return transfers


def calculate_minimum_transfers(trip: Trip) -> List[Dict]:
    """
    Calculate minimum number of transfers needed to settle all debts in a trip.
    Uses a greedy algorithm to minimize the number of transactions.
    
    Args:
        trip: Trip object
        
    Returns:
        List of transfer dictionaries with 'from_user', 'to_user', and 'amount'
    """
    # Calculate net balance for each user
    net_balances = defaultdict(Decimal)
    
    # Get all enabled transactions for this trip
    transactions = Transaction.objects.filter(
        trip=trip,
        is_enabled=True
    ).prefetch_related('members__user')
    
    for transaction in transactions:
        # Add amount to the person who paid
        net_balances[transaction.paid_by.id] += transaction.amount
        
        # Subtract from each person who owes
        for member in transaction.members.filter(is_included=True):
            net_balances[member.user.id] -= member.amount_owed
    
    # Separate creditors (positive balance) and debtors (negative balance)
    creditors = []
    debtors = []
    
    for user_id, balance in net_balances.items():
        if balance > 0:
            creditors.append((user_id, balance))
        elif balance < 0:
            debtors.append((user_id, -balance))  # Store as positive for easier calculation
    
    # Sort by amount (largest first)
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    
    # Calculate minimum transfers
    transfers = []
    creditor_index = 0
    debtor_index = 0
    
    while creditor_index < len(creditors) and debtor_index < len(debtors):
        creditor_id, creditor_amount = creditors[creditor_index]
        debtor_id, debtor_amount = debtors[debtor_index]
        
        # Transfer amount is the minimum of what creditor can give and debtor needs
        transfer_amount = min(creditor_amount, debtor_amount)
        
        if transfer_amount > 0:
            # Get user objects for the transfer
            try:
                from_user = User.objects.get(id=debtor_id)
                to_user = User.objects.get(id=creditor_id)
                
                transfers.append({
                    'from_user': {
                        'id': str(from_user.id),
                        'name': from_user.name,
                        'email': from_user.email
                    },
                    'to_user': {
                        'id': str(to_user.id),
                        'name': to_user.name,
                        'email': to_user.email
                    },
                    'amount': float(transfer_amount)
                })
            except User.DoesNotExist:
                pass
        
        # Update amounts
        creditors[creditor_index] = (creditor_id, creditor_amount - transfer_amount)
        debtors[debtor_index] = (debtor_id, debtor_amount - transfer_amount)
        
        # Move to next creditor/debtor if current one is settled
        if creditors[creditor_index][1] == 0:
            creditor_index += 1
        if debtors[debtor_index][1] == 0:
            debtor_index += 1
    
    return transfers


def calculate_user_balance_in_trip(user: User, trip: Trip) -> Decimal:
    """
    Calculate the net balance for a specific user in a trip.
    Positive balance means user is owed money, negative means user owes money.
    
    Args:
        user: User object
        trip: Trip object
        
    Returns:
        Decimal representing the net balance
    """
    balance = Decimal('0')
    
    # Get all enabled transactions for this trip
    transactions = Transaction.objects.filter(
        trip=trip,
        is_enabled=True
    ).prefetch_related('members')
    
    for transaction in transactions:
        # Add amount if user paid
        if transaction.paid_by == user:
            balance += transaction.amount
        
        # Subtract amount if user owes
        try:
            member = transaction.members.get(user=user, is_included=True)
            balance -= member.amount_owed
        except TransactionMember.DoesNotExist:
            pass
    
    return balance


def get_trip_summary(trip: Trip) -> Dict:
    """
    Get a summary of all balances and transactions for a trip.
    
    Args:
        trip: Trip object
        
    Returns:
        Dictionary with trip summary data
    """
    members = trip.members.filter(is_active=True)
    member_balances = {}
    total_spent = Decimal('0')
    total_transactions = 0
    
    for member in members:
        balance = calculate_user_balance_in_trip(member.user, trip)
        member_balances[str(member.user.id)] = {
            'user': {
                'id': str(member.user.id),
                'name': member.user.name,
                'email': member.user.email
            },
            'balance': float(balance)
        }
        
        # Calculate total spent by this user
        user_transactions = Transaction.objects.filter(
            trip=trip,
            paid_by=member.user,
            is_enabled=True
        )
        user_total = sum(t.amount for t in user_transactions)
        member_balances[str(member.user.id)]['total_spent'] = float(user_total)
        total_spent += user_total
    
    # Count total transactions
    total_transactions = Transaction.objects.filter(
        trip=trip,
        is_enabled=True
    ).count()
    
    # Calculate minimum transfers
    transfers = calculate_minimum_transfers(trip)
    
    return {
        'trip': {
            'id': str(trip.id),
            'name': trip.name,
            'description': trip.description,
            'owner': {
                'id': str(trip.owner.id),
                'name': trip.owner.name,
                'email': trip.owner.email
            }
        },
        'members': member_balances,
        'total_spent': float(total_spent),
        'total_transactions': total_transactions,
        'minimum_transfers': transfers
    }
