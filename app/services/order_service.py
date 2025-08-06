# app/services/order_service.py

from app.models.models import db, Account, Asset, Holding, Transaction, TransactionType, TransactionStatus
from .market_data_service import MarketDataService
from decimal import Decimal
from datetime import date

class OrderService:
    BROKERAGE_FEE = Decimal('1.00') # A flat $1.00 commission per trade

    @staticmethod
    def place_order(user_id: int, order_data: dict):
        """Processes a buy or sell order with advanced logic."""
        # --- 1. Validation ---
        required = ['account_id', 'ticker', 'quantity', 'order_type', 'transaction_type']
        if not all(field in order_data for field in required):
            raise ValueError(f"Missing required fields: {', '.join(required)}")

        order_type = order_data['order_type'].upper()
        if order_type not in ['MARKET', 'LIMIT', 'STOP_LOSS']:
            raise ValueError("Invalid order_type. Must be 'MARKET', 'LIMIT', or 'STOP_LOSS'.")
        
        transaction_type_str = order_data['transaction_type'].upper()
        if transaction_type_str not in ['BUY', 'SELL']:
            raise ValueError("Invalid transaction_type. Must be 'BUY' or 'SELL'.")
        # FIX: Convert the string from the API into a TransactionType enum member
        transaction_type = TransactionType[transaction_type_str]

        account = db.session.get(Account, order_data['account_id'])
        if not account: raise ValueError("Account not found.")

        quantity = Decimal(str(order_data['quantity']))
        if quantity <= 0: raise ValueError("Quantity must be positive.")

        asset = MarketDataService.find_or_create_asset(order_data['ticker'])
        current_price = asset.last_price
        if not current_price or current_price <= 0:
            # FIX: Removed stray object from the error message for clarity.
            raise ValueError(f"Could not retrieve a valid market price for {asset.ticker_symbol}.")

        # --- 2. Handle Pending Orders (LIMIT, STOP_LOSS) ---
        if order_type in ['LIMIT', 'STOP_LOSS']:
            trigger_price = Decimal(str(order_data.get('trigger_price', 0)))
            if trigger_price <= 0:
                raise ValueError("A valid trigger_price is required for LIMIT and STOP_LOSS orders.")
            
            pending_order = Transaction(
                account_id=account.id, asset_id=asset.id, transaction_type=transaction_type,
                status=TransactionStatus.PENDING, order_type=order_type, trigger_price=trigger_price,
                transaction_date=date.today(), quantity=quantity,
                total_amount=-(quantity * trigger_price), # Estimated amount
                description=f"Pending {order_type} {transaction_type.value} for {quantity} shares of {asset.ticker_symbol} at ${trigger_price}"
            )
            db.session.add(pending_order)
            db.session.commit()
            return pending_order

        # --- 3. Execute MARKET Order ---
        total_value = quantity * current_price
        
        transaction = Transaction(
            account_id=account.id, asset_id=asset.id, transaction_type=transaction_type,
            status=TransactionStatus.COMPLETED, order_type='MARKET', transaction_date=date.today(),
            quantity=quantity, price_per_unit=current_price, commission_fee=OrderService.BROKERAGE_FEE
        )

        if transaction_type == TransactionType.BUY:
            if account.balance < (total_value + OrderService.BROKERAGE_FEE):
                raise ValueError("Insufficient funds.")
            
            holding = Holding.query.filter_by(account_id=account.id, asset_id=asset.id).first()
            if not holding:
                holding = Holding(account_id=account.id, asset_id=asset.id, quantity=0, cost_basis=0)
                db.session.add(holding)
            
            holding.quantity += quantity
            holding.cost_basis += total_value
            account.balance -= (total_value + OrderService.BROKERAGE_FEE)
            transaction.total_amount = -(total_value)

        elif transaction_type == TransactionType.SELL:
            holding = Holding.query.filter_by(account_id=account.id, asset_id=asset.id).first()
            if not holding or holding.quantity < quantity:
                raise ValueError("Insufficient shares to sell.")

            cost_basis_per_share = holding.average_price
            realized_pnl = (quantity * current_price) - (quantity * cost_basis_per_share)
            transaction.realized_pnl = realized_pnl
            
            holding.cost_basis -= (quantity * cost_basis_per_share)
            holding.quantity -= quantity
            account.balance += (total_value - OrderService.BROKERAGE_FEE)
            transaction.total_amount = total_value
        
        db.session.add(transaction)
        db.session.commit()
        return transaction