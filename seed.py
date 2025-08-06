# seed.py

import random
from app import create_app
from app.models.models import db, User, Portfolio, Account, Asset, Holding, Transaction, Watchlist, WatchlistItem, AccountType, AssetType, TransactionType
from datetime import date, timedelta
from decimal import Decimal
import hashlib

def run_seed():
    """
    Populates the database with a large, realistic, and consistent dataset for a brokerage app,
    simulating several years of activity for a single user, with all dates relative to yesterday.
    """
    app = create_app(config_name='development')
    with app.app_context():
        print("Starting large database seed...")

        # --- 1. Drop and Recreate All Tables ---
        print("Dropping all database tables...")
        db.drop_all()
        print("Creating all database tables from models...")
        db.create_all()
        print("Tables created successfully.")

        # --- 2. Create a Sample User ---
        print("Creating a sample user...")
        password_hash = hashlib.sha256("password".encode()).hexdigest()
        user = User(username="testuser", email="test@example.com", password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        print(f"Created user '{user.username}' with ID: {user.id}.")

        # --- 3. Create Portfolio for the User ---
        portfolio = Portfolio(name='Main Portfolio', user_id=user.id)
        db.session.add(portfolio)
        db.session.commit()
        print(f"Created portfolio '{portfolio.name}' for user '{user.username}'.")

        # --- 4. Create a large set of Assets ---
        asset_data = {
            'AAPL': 'Apple Inc', 'MSFT': 'Microsoft Corp', 'GOOGL': 'Alphabet Inc.', 'TSLA': 'Tesla, Inc.',
            'AMZN': 'Amazon.com, Inc.', 'NVDA': 'NVIDIA Corporation', 'JPM': 'JPMorgan Chase & Co.',
            'JNJ': 'Johnson & Johnson', 'V': 'Visa Inc.', 'PG': 'Procter & Gamble Co.', 'UNH': 'UnitedHealth Group',
            'HD': 'The Home Depot, Inc.', 'MA': 'Mastercard Incorporated', 'BAC': 'Bank of America Corp',
            'PFE': 'Pfizer Inc.', 'DIS': 'The Walt Disney Company', 'ADBE': 'Adobe Inc.', 'CRM': 'Salesforce, Inc.',
            'NFLX': 'Netflix, Inc.', 'XOM': 'Exxon Mobil Corporation', 'T': 'AT&T Inc.', 'WMT': 'Walmart Inc.',
            'KO': 'The Coca-Cola Company', 'PEP': 'PepsiCo, Inc.', 'CSCO': 'Cisco Systems, Inc.',
            'INTC': 'Intel Corporation', 'VZ': 'Verizon Communications Inc.', 'ORCL': 'Oracle Corporation',
            'CVS': 'CVS Health Corporation', 'MCD': "McDonald's Corporation", 'BA': 'The Boeing Company',
            'CAT': 'Caterpillar Inc.', 'GS': 'The Goldman Sachs Group, Inc.', 'IBM': 'IBM Corporation',
            'NKE': 'NIKE, Inc.', 'SBUX': 'Starbucks Corporation', 'UBER': 'Uber Technologies, Inc.',
            'LYFT': 'Lyft, Inc.', 'PYPL': 'PayPal Holdings, Inc.', 'SQ': 'Block, Inc.', 'COIN': 'Coinbase Global, Inc.',
            'AMD': 'Advanced Micro Devices, Inc.', 'QCOM': 'QUALCOMM Incorporated', 'TXN': 'Texas Instruments Incorporated',
            'COST': 'Costco Wholesale Corporation', 'TGT': 'Target Corporation', 'LOW': "Lowe's Companies, Inc.",
            'CASH': 'US Dollar'
        }
        
        assets = {}
        for ticker, name in asset_data.items():
            if ticker == 'CASH':
                asset = Asset(ticker_symbol=ticker, name=name, asset_type=AssetType.CASH, last_price=Decimal('1.00'), previous_close_price=Decimal('1.00'))
            else:
                # Add realistic, hardcoded prices to reduce initial API dependency
                price = Decimal(random.uniform(50, 550))
                prev_close = price * Decimal(random.uniform(0.98, 1.02)) # +/- 2% change
                asset = Asset(ticker_symbol=ticker, name=name, asset_type=AssetType.STOCK, last_price=price, previous_close_price=prev_close)
            assets[ticker] = asset
            
        db.session.add_all(assets.values())
        db.session.commit()
        print(f"Created {len(assets)} assets with initial price data.")

        # --- 5. Create Accounts ---
        accounts = {
            'cash': Account(portfolio_id=portfolio.id, name='Primary Cash Account', account_type=AccountType.CASH, balance=Decimal('75000.00')),
            'brokerage': Account(portfolio_id=portfolio.id, name='Main Brokerage Account', account_type=AccountType.INVESTMENT),
            'roth_ira': Account(portfolio_id=portfolio.id, name='Roth IRA', account_type=AccountType.RETIREMENT)
        }
        db.session.add_all(accounts.values())
        db.session.commit()
        print(f"Created {len(accounts)} accounts.")

        # --- 6. Generate a reduced, realistic transaction history ---
        print("Generating transaction history...")
        holdings = {}
        transactions_to_add = []
        
        yesterday = date.today() - timedelta(days=1)
        start_date = yesterday - timedelta(days=2 * 365) # 2 years of history
        
        initial_deposit = Transaction(account_id=accounts['cash'].id, transaction_type=TransactionType.DEPOSIT, transaction_date=start_date, total_amount=Decimal('75000'), description='Initial capital deposit')
        transactions_to_add.append(initial_deposit)

        for i in range(50): # Generate ~50 core financial events
            random_date = start_date + timedelta(days=random.randint(1, (yesterday - start_date).days))
            event_type = random.choice(['TRADE', 'TRADE', 'TRADE', 'DIVIDEND']) # More focus on trading

            if event_type == 'TRADE':
                trade_type = 'BUY'
                ticker_to_trade = random.choice([t for t in assets if t != 'CASH'])
                asset_id = assets[ticker_to_trade].id
                
                if trade_type == 'BUY':
                    quantity = Decimal(random.randint(5, 25))
                    price = assets[ticker_to_trade].last_price * Decimal(random.uniform(0.8, 1.0)) # Simulate buying at a past, lower price
                    total_cost = quantity * price
                    if accounts['cash'].balance >= total_cost:
                        accounts['cash'].balance -= total_cost
                        if asset_id not in holdings:
                            holdings[asset_id] = {'quantity': Decimal(0), 'cost_basis': Decimal(0), 'account_id': accounts['brokerage'].id}
                        holdings[asset_id]['quantity'] += quantity
                        holdings[asset_id]['cost_basis'] += total_cost
                        transactions_to_add.append(Transaction(account_id=accounts['brokerage'].id, asset_id=asset_id, transaction_type=TransactionType.BUY, transaction_date=random_date, quantity=quantity, price_per_unit=price, total_amount=-total_cost, description=f'Market buy of {ticker_to_trade}'))

        db.session.add_all(transactions_to_add)
        print(f"Generated {len(transactions_to_add)} transactions.")

        # --- 7. Create Holdings from in-memory tracker ---
        holdings_to_add = [Holding(account_id=h['account_id'], asset_id=asset_id, quantity=h['quantity'], cost_basis=h['cost_basis']) for asset_id, h in holdings.items() if h['quantity'] > 0]
        db.session.add_all(holdings_to_add)
        print(f"Created {len(holdings_to_add)} final holding records.")

        # --- 8. Create Expanded Watchlists and Items ---
        print("Creating watchlists...")
        watchlist_names = ["Blue Chip Stocks", "Growth Tech", "Dividend Payers", "EV & Renewables", "Financials"]
        watchlists = {name: Watchlist(name=name, portfolio_id=portfolio.id) for name in watchlist_names}
        db.session.add_all(watchlists.values())
        db.session.commit()
        
        watchlist_items = [
            WatchlistItem(watchlist_id=watchlists["Blue Chip Stocks"].id, asset_id=assets['JNJ'].id),
            WatchlistItem(watchlist_id=watchlists["Blue Chip Stocks"].id, asset_id=assets['JPM'].id),
            WatchlistItem(watchlist_id=watchlists["Blue Chip Stocks"].id, asset_id=assets['PG'].id),
            WatchlistItem(watchlist_id=watchlists["Blue Chip Stocks"].id, asset_id=assets['HD'].id),
            WatchlistItem(watchlist_id=watchlists["Blue Chip Stocks"].id, asset_id=assets['UNH'].id),
            WatchlistItem(watchlist_id=watchlists["Blue Chip Stocks"].id, asset_id=assets['WMT'].id),
            WatchlistItem(watchlist_id=watchlists["Blue Chip Stocks"].id, asset_id=assets['KO'].id),
            WatchlistItem(watchlist_id=watchlists["Growth Tech"].id, asset_id=assets['TSLA'].id),
            WatchlistItem(watchlist_id=watchlists["Growth Tech"].id, asset_id=assets['NVDA'].id),
            WatchlistItem(watchlist_id=watchlists["Growth Tech"].id, asset_id=assets['AMZN'].id),
            WatchlistItem(watchlist_id=watchlists["Growth Tech"].id, asset_id=assets['NFLX'].id),
            WatchlistItem(watchlist_id=watchlists["Growth Tech"].id, asset_id=assets['CRM'].id),
            WatchlistItem(watchlist_id=watchlists["Growth Tech"].id, asset_id=assets['ADBE'].id),
            WatchlistItem(watchlist_id=watchlists["Growth Tech"].id, asset_id=assets['SQ'].id),
            WatchlistItem(watchlist_id=watchlists["Dividend Payers"].id, asset_id=assets['JNJ'].id),
            WatchlistItem(watchlist_id=watchlists["Dividend Payers"].id, asset_id=assets['PG'].id),
            WatchlistItem(watchlist_id=watchlists["Dividend Payers"].id, asset_id=assets['KO'].id),
            WatchlistItem(watchlist_id=watchlists["Dividend Payers"].id, asset_id=assets['PEP'].id),
            WatchlistItem(watchlist_id=watchlists["Dividend Payers"].id, asset_id=assets['T'].id),
            WatchlistItem(watchlist_id=watchlists["EV & Renewables"].id, asset_id=assets['TSLA'].id),
            WatchlistItem(watchlist_id=watchlists["Financials"].id, asset_id=assets['JPM'].id),
            WatchlistItem(watchlist_id=watchlists["Financials"].id, asset_id=assets['V'].id),
            WatchlistItem(watchlist_id=watchlists["Financials"].id, asset_id=assets['MA'].id),
            WatchlistItem(watchlist_id=watchlists["Financials"].id, asset_id=assets['BAC'].id),
            WatchlistItem(watchlist_id=watchlists["Financials"].id, asset_id=assets['GS'].id),
        ]
        db.session.add_all(watchlist_items)
        print(f"Created {len(watchlists)} watchlists with {len(watchlist_items)} items.")
        
        db.session.commit()
        print("\nDatabase seeded successfully! You can run 'python update_prices.py' to get the absolute latest prices.")

if __name__ == '__main__':
    run_seed()