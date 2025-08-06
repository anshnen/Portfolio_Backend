# app/services/order_service.py

from app.models.models import db, Account, Asset, Holding, Transaction, TransactionType, TransactionStatus
from .market_data_service import MarketDataService
from decimal import Decimal
from datetime import date

class OrderService:
    BROKERAGE_FEE = Decimal('1.00')

    @staticmethod
    def place_order(user_id: int, order_data: dict):
        required = ['account_id', 'ticker', 'quantity', 'order_type', 'transaction_type']
        if not all(field in order_data for field in required):
            raise ValueError(f"Missing required fields: {', '.join(required)}")

        order_type = order_data['order_type'].upper()
        if order_type not in ['MARKET', 'LIMIT', 'STOP_LOSS']:
            raise ValueError("Invalid order_type.")
        
        transaction_type_str = order_data['transaction_type'].upper()
        transaction_type = TransactionType[transaction_type_str]

        account = db.session.get(Account, order_data['account_id'])
        if not account: raise ValueError("Account not found.")

        quantity = Decimal(str(order_data['quantity']))
        if quantity <= 0: raise ValueError("Quantity must be positive.")

        asset = MarketDataService.find_or_create_asset(order_data['ticker'])
        current_price = asset.last_price
        if not current_price or current_price <= 0:
            raise ValueError(f"Could not retrieve a valid market price for {asset.ticker_symbol}.")

        if order_type in ['LIMIT', 'STOP_LOSS']:
            trigger_price = Decimal(str(order_data.get('trigger_price', 0)))
            if trigger_price <= 0:
                raise ValueError("A valid trigger_price is required for LIMIT and STOP_LOSS orders.")
            
            pending_order = Transaction(
                account_id=account.id, asset_id=asset.id, transaction_type=transaction_type,
                status=TransactionStatus.PENDING, order_type=order_type, trigger_price=trigger_price,
                transaction_date=date.today(), quantity=quantity,
                total_amount=-(quantity * trigger_price),
                description=f"Pending {order_type} {transaction_type.value} for {quantity} shares of {asset.ticker_symbol} at ${trigger_price}"
            )
            db.session.add(pending_order)
            db.session.commit()
            return pending_order

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
