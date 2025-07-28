from app import create_app
from app.models.models import db, Portfolio, Account, Asset, Holding, Transaction
from datetime import date, timedelta
from decimal import Decimal

def run_seed():

    app = create_app(config_name='development')
    with app.app_context():
        print("Starting database seed...")

        # --- 1. Clear existing data ---
        print("Clearing old data...")
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
        db.session.commit() # Commit to get the portfolio ID
        print(f"Created portfolio '{portfolio.name}'.")

        # --- 3. Create Assets ---
        assets = {
            'AAPL': Asset(ticker_symbol='AAPL', name='Apple Inc', asset_type='STOCK', last_price=Decimal('171.50'), previous_close_price=Decimal('170.00')),
            'MSFT': Asset(ticker_symbol='MSFT', name='Microsoft Corp', asset_type='STOCK', last_price=Decimal('427.00'), previous_close_price=Decimal('430.00')),
            'GOOGL': Asset(ticker_symbol='GOOGL', name='Alphabet Inc.', asset_type='STOCK', last_price=Decimal('175.20'), previous_close_price=Decimal('174.90')),
            'TSLA': Asset(ticker_symbol='TSLA', name='Tesla, Inc.', asset_type='STOCK', last_price=Decimal('180.01'), previous_close_price=Decimal('181.50')),
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
            # Income: +18,665
            Transaction(account_id=accounts['checking'].id, transaction_type='DEPOSIT', transaction_date=date.today() - timedelta(days=10), total_amount=Decimal('10000'), description='Salary'),
            Transaction(account_id=accounts['fidelity'].id, asset_id=assets['AAPL'].id, transaction_type='DIVIDEND', transaction_date=date.today() - timedelta(days=5), total_amount=Decimal('8665')),
            # Spending: -42,500
            Transaction(account_id=accounts['checking'].id, transaction_type='WITHDRAWAL', transaction_date=date.today() - timedelta(days=15), total_amount=Decimal('-42500'), description='Mortgage Payment')
        ]
        db.session.add_all(transactions)
        db.session.commit()
        print(f"Created {len(transactions)} transactions.")

        print("\nDatabase seeded successfully!")

if __name__ == '__main__':
    run_seed()