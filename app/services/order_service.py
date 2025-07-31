from app.models.models import db, Account, Asset, Holding, Transaction
from .market_data_service import MarketDataService
from decimal import Decimal
from datetime import date

class OrderService:
    @staticmethod
    def place_order(user_id: int, order_data: dict):
        """Processes a buy or sell order for a user."""
        # --- Validation ---
        required_fields = ['account_id', 'ticker', 'quantity', 'order_type']
        if not all(field in order_data for field in required_fields):
            raise ValueError("Missing required fields for the order.")

        order_type = order_data['order_type'].upper()
        if order_type not in ['BUY', 'SELL']:
            raise ValueError("Invalid order type. Must be 'BUY' or 'SELL'.")

        account = Account.query.get(order_data['account_id'])
        # In a real multi-user app, you'd also check if account.portfolio.user_id == user_id
        if not account:
            raise ValueError("Account not found.")

        asset = MarketDataService.find_or_create_asset(order_data['ticker'])
        quantity = Decimal(str(order_data['quantity']))
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        # Use the latest price from our database
        current_price = asset.last_price
        if not current_price:
            raise ValueError(f"Could not retrieve current price for {asset.ticker_symbol}.")

        total_cost = quantity * current_price

        # --- Execution Logic ---
        if order_type == 'BUY':
            if account.balance < total_cost:
                raise ValueError("Insufficient funds to place buy order.")
            
            # Update or create holding
            holding = Holding.query.filter_by(account_id=account.id, asset_id=asset.id).first()
            if not holding:
                holding = Holding(account_id=account.id, asset_id=asset.id, quantity=0, cost_basis=0)
                db.session.add(holding)
            
            holding.quantity += quantity
            holding.cost_basis += total_cost
            account.balance -= total_cost

        elif order_type == 'SELL':
            holding = Holding.query.filter_by(account_id=account.id, asset_id=asset.id).first()
            if not holding or holding.quantity < quantity:
                raise ValueError("Insufficient shares to place sell order.")

            # Simple cost basis reduction
            cost_basis_per_share = holding.cost_basis / holding.quantity
            holding.cost_basis -= (quantity * cost_basis_per_share)
            holding.quantity -= quantity
            account.balance += total_cost
        
        # Create a transaction record
        transaction = Transaction(
            account_id=account.id,
            asset_id=asset.id,
            transaction_type=order_type,
            status='COMPLETED',
            transaction_date=date.today(),
            quantity=quantity,
            price_per_unit=current_price,
            total_amount=total_cost if order_type == 'SELL' else -total_cost
        )
        db.session.add(transaction)
        db.session.commit()

        return transaction