from app import create_app
from app.models.models import db, Portfolio, Account, Asset, Holding, Transaction, Watchlist, WatchlistItem
from datetime import date, timedelta
from decimal import Decimal

def run_seed():
    """
    Populates the database with a realistic and consistent dataset for development and testing.
    This script is idempotent - it clears old data before adding new data.
    """
    app = create_app(config_name='development')
    with app.app_context():
        print("Starting database seed...")

        # --- 1. Clear Existing Data (in reverse order of creation) ---
        print("Clearing old data...")
        db.session.query(WatchlistItem).delete()
        db.session.query(Watchlist).delete()
        db.session.query(Transaction).delete()
        db.session.query(Holding).delete()
        db.session.query(Account).delete()
        db.session.query(Asset).delete()
        db.session.query(Portfolio).delete()
        db.session.commit()
        print("Old data cleared.")

        # --- 2. Create Portfolio ---
        portfolio = Portfolio(name='Main Portfolio')
        db.session.add(portfolio)
        db.session.commit()
        print(f"Created portfolio '{portfolio.name}'.")

        # --- 3. Create Assets ---
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

        # --- 4. Create Accounts ---
        accounts = {
            'checking': Account(portfolio_id=portfolio.id, name='Wells Fargo Checking', institution='Wells Fargo', account_type='CASH', balance=Decimal('309.13')),
            'savings': Account(portfolio_id=portfolio.id, name='Wells Fargo Savings', institution='Wells Fargo', account_type='CASH', balance=Decimal('2000.67')),
            'fidelity': Account(portfolio_id=portfolio.id, name='Fidelity Brokerage', institution='Fidelity', account_type='INVESTMENT'),
            'pershing': Account(portfolio_id=portfolio.id, name='Pershing IRA', institution='Pershing', account_type='RETIREMENT')
        }
        db.session.add_all(accounts.values())
        db.session.commit()
        print(f"Created {len(accounts)} accounts.")

        # --- 5. Create Holdings ---
        holdings = [
            Holding(account_id=accounts['fidelity'].id, asset_id=assets['AAPL'].id, quantity=Decimal('150.5'), cost_basis=Decimal('22500.00')),
            Holding(account_id=accounts['fidelity'].id, asset_id=assets['MSFT'].id, quantity=Decimal('50'), cost_basis=Decimal('15000.00')),
            Holding(account_id=accounts['pershing'].id, asset_id=assets['GOOGL'].id, quantity=Decimal('200'), cost_basis=Decimal('20000.00')),
            Holding(account_id=accounts['pershing'].id, asset_id=assets['TSLA'].id, quantity=Decimal('100'), cost_basis=Decimal('25000.00'))
        ]
        db.session.add_all(holdings)
        db.session.commit()
        print(f"Created {len(holdings)} holdings.")

        # --- 6. Create Transactions ---
        transactions = [
            Transaction(account_id=accounts['checking'].id, transaction_type='DEPOSIT', transaction_date=date.today() - timedelta(days=10), total_amount=Decimal('10000'), description='Salary'),
            Transaction(account_id=accounts['fidelity'].id, asset_id=assets['AAPL'].id, transaction_type='DIVIDEND', transaction_date=date.today() - timedelta(days=5), total_amount=Decimal('8665')),
            Transaction(account_id=accounts['checking'].id, transaction_type='WITHDRAWAL', transaction_date=date.today() - timedelta(days=15), total_amount=Decimal('-42500'), description='Mortgage Payment')
        ]
        db.session.add_all(transactions)
        db.session.commit()
        print(f"Created {len(transactions)} transactions.")

        # --- 7. Create Watchlists and Items ---
        print("Creating watchlists...")
        watchlist1 = Watchlist(name="Tech Giants", portfolio_id=portfolio.id)
        watchlist2 = Watchlist(name="Dividend Stocks", portfolio_id=portfolio.id)
        watchlist3 = Watchlist(name="Growth & EV", portfolio_id=portfolio.id)
        db.session.add_all([watchlist1, watchlist2, watchlist3])
        db.session.commit() # Commit to get watchlist IDs

        watchlist_items = [
            # Tech Giants
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['AAPL'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['MSFT'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['GOOGL'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['AMZN'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['NVDA'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['V'].id),
            # Dividend Stocks
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['JNJ'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['JPM'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['PG'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['MSFT'].id),
            # Growth & EV
            WatchlistItem(watchlist_id=watchlist3.id, asset_id=assets['TSLA'].id),
            WatchlistItem(watchlist_id=watchlist3.id, asset_id=assets['NVDA'].id),
            WatchlistItem(watchlist_id=watchlist3.id, asset_id=assets['AMZN'].id)
        ]
        db.session.add_all(watchlist_items)
        db.session.commit()
        print(f"Created 3 watchlists with {len(watchlist_items)} items.")

        print("\nDatabase seeded successfully! Run 'python update_prices.py' to fetch initial market data.")

if __name__ == '__main__':
    run_seed()