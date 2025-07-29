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
def update_transaction(transaction_id: int, data: dict):
    """Updates an existing transaction and, if applicable, adjusts holdings and account balance."""
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        raise ValueError("Transaction not found.")

    original_amount = transaction.total_amount
    original_quantity = transaction.quantity
    original_price = transaction.price_per_unit
    original_type = transaction.transaction_type
    account = transaction.account

    # Update fields (only if provided in the input data)
    transaction.description = data.get('description', transaction.description)
    transaction.transaction_type = data.get('transaction_type', transaction.transaction_type).upper()
    transaction.transaction_date = datetime.strptime(data.get('transaction_date', transaction.transaction_date.strftime('%Y-%m-%d')), '%Y-%m-%d').date()
    transaction.total_amount = Decimal(str(data.get('total_amount', transaction.total_amount)))

    # Adjust account balance (remove old amount, add new)
    account.balance -= original_amount
    account.balance += transaction.total_amount

    # Handle asset-related updates if applicable
    if transaction.transaction_type in ['BUY', 'SELL']:
        asset = transaction.asset
        if not asset and 'asset_ticker' in data:
            asset = Asset.query.filter_by(ticker_symbol=data['asset_ticker'].upper()).first()
            if not asset:
                raise ValueError("Asset not found.")
            transaction.asset_id = asset.id

        quantity = Decimal(str(data.get('quantity', transaction.quantity)))
        price_per_unit = Decimal(str(data.get('price_per_unit', transaction.price_per_unit)))

        holding = Holding.query.filter_by(account_id=account.id, asset_id=transaction.asset_id).first()

        # Revert previous effect on holdings
        if original_type == 'BUY':
            holding.quantity -= original_quantity
            holding.cost_basis -= original_quantity * original_price
        elif original_type == 'SELL':
            holding.quantity += original_quantity
            holding.cost_basis += original_quantity * (original_price if holding.quantity != 0 else 0)

        # Apply new values
        transaction.quantity = quantity
        transaction.price_per_unit = price_per_unit

        if transaction.transaction_type == 'BUY':
            holding.quantity += quantity
            holding.cost_basis += quantity * price_per_unit
        elif transaction.transaction_type == 'SELL':
            if holding.quantity < quantity:
                raise ValueError("Insufficient shares to sell.")
            cost_basis_per_share = holding.cost_basis / holding.quantity if holding.quantity else 0
            holding.cost_basis -= quantity * cost_basis_per_share
            holding.quantity -= quantity

    db.session.commit()
    return transaction

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