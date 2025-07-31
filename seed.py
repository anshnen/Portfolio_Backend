# seed.py

from app import create_app
from app.models.models import db, User, Portfolio, Account, Asset, Holding, Transaction, Watchlist, WatchlistItem
from datetime import date, timedelta
from decimal import Decimal
# In a real app, you'd use a library like Werkzeug for password hashing
import hashlib 

def run_seed():
    """
    Populates the database with a realistic and consistent dataset for a brokerage app.
    This script is idempotent - it drops and recreates the entire schema.
    """
    app = create_app(config_name='development')
    with app.app_context():
        print("Starting database seed...")

        # --- 1. Drop and Recreate All Tables ---
        print("Dropping all database tables...")
        db.drop_all()
        print("Creating all database tables from models...")
        db.create_all()
        print("Tables created successfully.")

        # --- 2. Create a Sample User ---
        print("Creating a sample user...")
        # Simple hashing for seed script; use Werkzeug/bcrypt in a real app
        password_hash = hashlib.sha256("password".encode()).hexdigest()
        user = User(username="testuser", email="test@example.com", password_hash=password_hash)
        db.session.add(user)
        db.session.commit() # Commit to get the user ID
        print(f"Created user '{user.username}' with ID: {user.id}.")

        # --- 3. Create Portfolio for the User ---
        # FIX: Pass the user_id when creating the portfolio
        portfolio = Portfolio(name='Main Portfolio', user_id=user.id)
        db.session.add(portfolio)
        db.session.commit()
        print(f"Created portfolio '{portfolio.name}' for user '{user.username}'.")

        # --- 4. Create Assets ---
        assets = {
            'AAPL': Asset(ticker_symbol='AAPL', name='Apple Inc', asset_type='STOCK'),
            'MSFT': Asset(ticker_symbol='MSFT', name='Microsoft Corp', asset_type='STOCK'),
            'GOOGL': Asset(ticker_symbol='GOOGL', name='Alphabet Inc.', asset_type='STOCK'),
            'TSLA': Asset(ticker_symbol='TSLA', name='Tesla, Inc.', asset_type='STOCK'),
            'AMZN': Asset(ticker_symbol='AMZN', name='Amazon.com, Inc.', asset_type='STOCK'),
            'NVDA': Asset(ticker_symbol='NVDA', name='NVIDIA Corporation', asset_type='STOCK'),
            'JPM': Asset(ticker_symbol='JPM', name='JPMorgan Chase & Co.', asset_type='STOCK'),
            'JNJ': Asset(ticker_symbol='JNJ', name='Johnson & Johnson', asset_type='STOCK'),
            'V': Asset(ticker_symbol='V', name='Visa Inc.', asset_type='STOCK'),
            'PG': Asset(ticker_symbol='PG', name='Procter & Gamble Co.', asset_type='STOCK'),
            'CASH': Asset(ticker_symbol='USD', name='US Dollar', asset_type='CASH', last_price=Decimal('1.00'), previous_close_price=Decimal('1.00'))
        }
        db.session.add_all(assets.values())
        db.session.commit()
        print(f"Created {len(assets)} assets.")

        # --- 5. Create Accounts ---
        accounts = {
            'cash': Account(portfolio_id=portfolio.id, name='Cash Account', account_type='CASH', balance=Decimal('100000.00')),
            'brokerage': Account(portfolio_id=portfolio.id, name='Brokerage Account', account_type='INVESTMENT')
        }
        db.session.add_all(accounts.values())
        db.session.commit()
        print(f"Created {len(accounts)} accounts.")

        # --- 6. Create Holdings ---
        holdings = [
            Holding(account_id=accounts['brokerage'].id, asset_id=assets['AAPL'].id, quantity=Decimal('150.5'), cost_basis=Decimal('22500.00')),
            Holding(account_id=accounts['brokerage'].id, asset_id=assets['MSFT'].id, quantity=Decimal('50'), cost_basis=Decimal('15000.00')),
        ]
        db.session.add_all(holdings)
        db.session.commit()
        print(f"Created {len(holdings)} holdings.")

        # --- 7. Create Transactions ---
        transactions = [
            Transaction(account_id=accounts['cash'].id, transaction_type='DEPOSIT', transaction_date=date.today() - timedelta(days=30), total_amount=Decimal('100000'), description='Initial deposit'),
        ]
        db.session.add_all(transactions)
        db.session.commit()
        print(f"Created {len(transactions)} transactions.")

        # --- 8. Create Watchlists and Items ---
        print("Creating watchlists...")
        watchlist1 = Watchlist(name="Tech Giants", portfolio_id=portfolio.id)
        watchlist2 = Watchlist(name="Value Stocks", portfolio_id=portfolio.id)
        db.session.add_all([watchlist1, watchlist2])
        db.session.commit()

        watchlist_items = [
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['GOOGL'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['AMZN'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['NVDA'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['JNJ'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['JPM'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['PG'].id),
        ]
        db.session.add_all(watchlist_items)
        db.session.commit()
        print(f"Created 2 watchlists with {len(watchlist_items)} items.")

        print("\nDatabase seeded successfully! Run 'python update_prices.py' to fetch initial market data.")

if __name__ == '__main__':
    run_seed()