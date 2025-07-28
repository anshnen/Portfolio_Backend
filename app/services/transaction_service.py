# app/services/transaction_service.py

from datetime import datetime
from decimal import Decimal
from app.models.models import db, Account, Asset, Holding, Transaction

def add_transaction(data: dict):

    # --- Data Validation ---
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

    # --- Logic for specific transaction types ---
    if transaction_type in ['BUY', 'SELL']:
        if not all(field in data for field in ['asset_ticker', 'quantity', 'price_per_unit']):
            raise ValueError("Asset ticker, quantity, and price are required for BUY/SELL transactions.")
        
        asset = Asset.query.filter_by(ticker_symbol=data['asset_ticker'].upper()).first()
        if not asset:
            # In a real app, you might create the asset here or fetch its details
            raise ValueError("Asset not found.")

        new_transaction.asset_id = asset.id
        new_transaction.quantity = Decimal(str(data['quantity']))
        new_transaction.price_per_unit = Decimal(str(data['price_per_unit']))
        
        # Update holding record
        holding = Holding.query.filter_by(account_id=account.id, asset_id=asset.id).first()
        if transaction_type == 'BUY':
            if not holding:
                holding = Holding(account_id=account.id, asset_id=asset.id, quantity=0, cost_basis=0)
                db.session.add(holding)
            holding.quantity += new_transaction.quantity
            holding.cost_basis += (new_transaction.quantity * new_transaction.price_per_unit)
        else: # SELL
            if not holding or holding.quantity < new_transaction.quantity:
                raise ValueError("Insufficient shares to sell.")
            # Simple cost basis reduction - more complex methods like FIFO/LIFO could be implemented
            cost_basis_per_share = holding.cost_basis / holding.quantity
            holding.cost_basis -= (new_transaction.quantity * cost_basis_per_share)
            holding.quantity -= new_transaction.quantity
    
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
            "transaction_date": t.transaction_date.isoformat(),
            "total_amount": float(t.total_amount),
            "description": t.description,
            "asset_ticker": t.asset.ticker_symbol if t.asset else None,
            "quantity": float(t.quantity) if t.quantity else None,
            "price_per_unit": float(t.price_per_unit) if t.price_per_unit else None
        } for t in transactions
    ]