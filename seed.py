# seed.py

import random
from app import create_app
from app.models.models import db, User, Portfolio, Account, Asset, Holding, Transaction, Watchlist, WatchlistItem
from datetime import date, timedelta
from decimal import Decimal
import hashlib

def run_seed():
    """
    Populates the database with a large, realistic, and consistent dataset for a brokerage app,
    simulating several years of activity for a single user.
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
            'CVS': 'CVS Health Corporation', 'MCD': "McDonald's Corporation",
            'CASH': 'US Dollar'
        }
        assets = {ticker: Asset(ticker_symbol=ticker, name=name, asset_type='CASH' if ticker == 'CASH' else 'STOCK') for ticker, name in asset_data.items()}
        db.session.add_all(assets.values())
        db.session.commit()
        print(f"Created {len(assets)} assets.")

        # --- 5. Create Accounts ---
        accounts = {
            'cash': Account(portfolio_id=portfolio.id, name='Primary Cash Account', account_type='CASH', balance=Decimal('50000.00')),
            'brokerage': Account(portfolio_id=portfolio.id, name='Main Brokerage Account', account_type='INVESTMENT'),
            'roth_ira': Account(portfolio_id=portfolio.id, name='Roth IRA', account_type='RETIREMENT')
        }
        db.session.add_all(accounts.values())
        db.session.commit()
        print(f"Created {len(accounts)} accounts.")

        # --- 6. Generate a large, realistic transaction history ---
        print("Generating transaction history...")
        holdings = {} # In-memory tracker for current holdings
        transactions_to_add = []
        
        start_date = date.today() - timedelta(days=3 * 365) # 3 years of history
        
        # Initial Deposit
        initial_deposit = Transaction(account_id=accounts['cash'].id, transaction_type='DEPOSIT', transaction_date=start_date, total_amount=Decimal('50000'), description='Initial capital deposit')
        transactions_to_add.append(initial_deposit)

        for i in range(100): # Generate ~100 core financial events
            # Simulate a random date within the last 3 years
            random_date = start_date + timedelta(days=random.randint(1, 3 * 365))
            event_type = random.choice(['SALARY', 'EXPENSE', 'TRADE', 'DIVIDEND'])

            if event_type == 'SALARY':
                salary = Decimal(random.uniform(2500, 4000))
                accounts['cash'].balance += salary
                transactions_to_add.append(Transaction(account_id=accounts['cash'].id, transaction_type='DEPOSIT', transaction_date=random_date, total_amount=salary, description='Monthly Salary'))
            
            elif event_type == 'EXPENSE':
                expense = Decimal(random.uniform(500, 2000))
                accounts['cash'].balance -= expense
                transactions_to_add.append(Transaction(account_id=accounts['cash'].id, transaction_type='WITHDRAWAL', transaction_date=random_date, total_amount=-expense, description='Living Expense'))

            elif event_type == 'TRADE':
                trade_type = random.choice(['BUY', 'SELL'])
                ticker_to_trade = random.choice([t for t in assets if t != 'CASH'])
                asset_id = assets[ticker_to_trade].id
                
                if trade_type == 'BUY':
                    quantity = Decimal(random.randint(10, 50))
                    price = Decimal(random.uniform(50, 500))
                    total_cost = quantity * price
                    if accounts['cash'].balance >= total_cost:
                        accounts['cash'].balance -= total_cost
                        # Update holdings in memory
                        if asset_id not in holdings:
                            holdings[asset_id] = {'quantity': Decimal(0), 'cost_basis': Decimal(0), 'account_id': accounts['brokerage'].id}
                        holdings[asset_id]['quantity'] += quantity
                        holdings[asset_id]['cost_basis'] += total_cost
                        transactions_to_add.append(Transaction(account_id=accounts['brokerage'].id, asset_id=asset_id, transaction_type='BUY', transaction_date=random_date, quantity=quantity, price_per_unit=price, total_amount=-total_cost, description=f'Market buy of {ticker_to_trade}'))
                
                elif trade_type == 'SELL' and asset_id in holdings and holdings[asset_id]['quantity'] > 0:
                    quantity_to_sell = Decimal(random.randint(1, int(holdings[asset_id]['quantity'])))
                    price = Decimal(random.uniform(50, 500))
                    total_proceeds = quantity_to_sell * price
                    accounts['cash'].balance += total_proceeds
                    # Update holdings in memory
                    avg_price = holdings[asset_id]['cost_basis'] / holdings[asset_id]['quantity']
                    holdings[asset_id]['cost_basis'] -= (quantity_to_sell * avg_price)
                    holdings[asset_id]['quantity'] -= quantity_to_sell
                    transactions_to_add.append(Transaction(account_id=accounts['brokerage'].id, asset_id=asset_id, transaction_type='SELL', transaction_date=random_date, quantity=quantity_to_sell, price_per_unit=price, total_amount=total_proceeds, description=f'Market sell of {ticker_to_trade}'))

            elif event_type == 'DIVIDEND' and holdings:
                asset_id_to_receive_dividend = random.choice(list(holdings.keys()))
                ticker = next(t for t, a in assets.items() if a.id == asset_id_to_receive_dividend)
                dividend_amount = holdings[asset_id_to_receive_dividend]['quantity'] * Decimal(random.uniform(0.1, 1.5))
                accounts['cash'].balance += dividend_amount
                transactions_to_add.append(Transaction(account_id=accounts['cash'].id, asset_id=asset_id_to_receive_dividend, transaction_type='DIVIDEND', transaction_date=random_date, total_amount=dividend_amount, description=f'Dividend from {ticker}'))

        db.session.add_all(transactions_to_add)
        print(f"Generated {len(transactions_to_add)} transactions.")

        # --- 7. Create Holdings from in-memory tracker ---
        holdings_to_add = [Holding(account_id=h['account_id'], asset_id=asset_id, quantity=h['quantity'], cost_basis=h['cost_basis']) for asset_id, h in holdings.items() if h['quantity'] > 0]
        db.session.add_all(holdings_to_add)
        print(f"Created {len(holdings_to_add)} final holding records.")

        # --- 8. Create Watchlists and Items ---
        print("Creating watchlists...")
        watchlist1 = Watchlist(name="Blue Chip Stocks", portfolio_id=portfolio.id)
        watchlist2 = Watchlist(name="Growth Tech", portfolio_id=portfolio.id)
        watchlist3 = Watchlist(name="Potential Buys", portfolio_id=portfolio.id)
        db.session.add_all([watchlist1, watchlist2, watchlist3])
        db.session.commit()
        
        watchlist_items = [
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['JNJ'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['JPM'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['PG'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['HD'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['UNH'].id),
            WatchlistItem(watchlist_id=watchlist1.id, asset_id=assets['WMT'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['TSLA'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['NVDA'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['AMZN'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['NFLX'].id),
            WatchlistItem(watchlist_id=watchlist2.id, asset_id=assets['CRM'].id),
            WatchlistItem(watchlist_id=watchlist3.id, asset_id=assets['DIS'].id),
            WatchlistItem(watchlist_id=watchlist3.id, asset_id=assets['PFE'].id),
            WatchlistItem(watchlist_id=watchlist3.id, asset_id=assets['T'].id),
        ]
        db.session.add_all(watchlist_items)
        print(f"Created 3 watchlists with {len(watchlist_items)} items.")
        
        db.session.commit()
        print("\nDatabase seeded successfully! Run 'python update_prices.py' to fetch initial market data.")

if __name__ == '__main__':
    run_seed()