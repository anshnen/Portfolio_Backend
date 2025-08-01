# app/services/transaction_service.py

from datetime import datetime
from decimal import Decimal
from app.models.models import db, Account, Asset, Holding, Transaction

def add_transaction(data: dict):
    """
    Core business logic to add a new transaction.
    Note: This is a simplified version. For BUY/SELL, the OrderService should be used.
    """
    required_fields = ['account_id', 'transaction_type', 'total_amount', 'transaction_date']
    if not all(field in data for field in required_fields):
        raise ValueError("Missing required fields for transaction.")

    account = Account.query.get(data['account_id'])
    if not account:
        raise ValueError("Account not found.")

    transaction_type = data['transaction_type'].upper()
    total_amount = Decimal(str(data['total_amount']))
    
    new_transaction = Transaction(
        account_id=account.id,
        transaction_type=transaction_type,
        total_amount=total_amount,
        transaction_date=datetime.strptime(data['transaction_date'], '%Y-%m-%d').date(),
        description=data.get('description')
    )
    
    # Update cash balance of the account
    account.balance += total_amount

    db.session.add(new_transaction)
    db.session.commit()
    
    return new_transaction

def get_transactions_by_account(account_id: int):
    """Retrieves all transactions for a given account, formatted for API response."""
    transactions = Transaction.query.filter_by(account_id=account_id).order_by(Transaction.transaction_date.desc()).all()
    
    return [
        {
            "id": t.id,
            "transaction_type": t.transaction_type,
            "status": t.status,
            "order_type": t.order_type,
            "transaction_date": t.transaction_date.isoformat(),
            "total_amount": float(t.total_amount),
            "description": t.description,
            "asset_ticker": t.asset.ticker_symbol if t.asset else None,
            "quantity": float(t.quantity) if t.quantity else None,
            "price_per_unit": float(t.price_per_unit) if t.price_per_unit else None,
            "realized_pnl": float(t.realized_pnl) if t.realized_pnl else None
        } for t in transactions
    ]

def update_transaction(transaction_id: int, data: dict):
    """
    Updates an existing transaction.
    WARNING: Modifying historical financial records is generally discouraged.
    This function is provided for flexibility but should be used with caution.
    It does not recalculate balances or holdings based on the change.
    """
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        raise ValueError("Transaction not found.")

    # Update fields if they are provided in the request data
    if 'description' in data:
        transaction.description = data['description']
    if 'transaction_date' in data:
        transaction.transaction_date = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
    
    # Add other updatable fields as needed, but be cautious about changing financial values.

    db.session.commit()
    return transaction