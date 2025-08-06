# tests/test_services/test_portfolio_service.py

from decimal import Decimal
from app.services.portfolio_service import get_portfolio_summary, get_detailed_holdings
from app.models.models import User, Portfolio, Account, Asset, Holding, Transaction, TransactionType, AssetType
from datetime import date

def test_get_portfolio_summary_logic(db):
    """
    GIVEN a portfolio with a single account, holdings, and transactions
    WHEN the get_portfolio_summary service function is called
    THEN it should return a dictionary with accurately calculated metrics
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    # FIX: Create only a single account for all activities
    account = Account(name="Primary Account", balance=Decimal("10000"), portfolio=portfolio)
    
    aapl = Asset(ticker_symbol="AAPL", name="Apple", asset_type=AssetType.STOCK, last_price=Decimal("175"), previous_close_price=Decimal("170"), sector="Tech")
    msft = Asset(ticker_symbol="MSFT", name="Microsoft", asset_type=AssetType.STOCK, last_price=Decimal("300"), previous_close_price=Decimal("310"), sector="Tech")

    # FIX: Associate holdings with the single account
    h_aapl = Holding(account=account, asset=aapl, quantity=10, cost_basis=1500) # Market Value = 1750
    h_msft = Holding(account=account, asset=msft, quantity=5, cost_basis=1600)  # Market Value = 1500

    # FIX: Associate cash flow transactions with the single account
    t1 = Transaction(account=account, transaction_type=TransactionType.DEPOSIT, total_amount=5000, transaction_date=date.today())
    t2 = Transaction(account=account, transaction_type=TransactionType.WITHDRAWAL, total_amount=-2000, transaction_date=date.today())

    db.session.add_all([user, portfolio, account, aapl, msft, h_aapl, h_msft, t1, t2])
    db.session.commit()

    # ACT
    summary, error = get_portfolio_summary(portfolio.id)

    # ASSERT
    assert error is None
    # Net Worth = 10000 (cash) + 1750 (aapl) + 1500 (msft) = 13250
    assert summary['net_worth'] == 13250.0
    # Today's Change = (175-170)*10 + (300-310)*5 = 50 - 50 = 0
    performance_data = summary.get('performance', {})
    assert performance_data.get('todays_change_amount') == 0.0
    
    # The account summary should reflect the single account
    account_data = summary.get('account', {})
    assert account_data is not None
    assert account_data.get('name') == "Primary Account"


def test_get_detailed_holdings_logic(db):
    """
    GIVEN a portfolio with holdings in a single account
    WHEN get_detailed_holdings is called
    THEN it should return a list of holdings with correct calculations
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    # FIX: Create only a single account
    account = Account(name="Primary Account", portfolio=portfolio)
    # FIX: Added the required 'asset_type' field.
    aapl = Asset(ticker_symbol="AAPL", name="Apple", asset_type=AssetType.STOCK, last_price=Decimal("175"))
    h_aapl = Holding(account=account, asset=aapl, quantity=10, cost_basis=1500)
    db.session.add_all([user, portfolio, account, aapl, h_aapl])
    db.session.commit()

    # ACT
    holdings, error = get_detailed_holdings(portfolio.id)

    # ASSERT
    assert error is None
    assert len(holdings) == 1
    holding = holdings[0]
    assert holding['ticker_symbol'] == 'AAPL'
    assert holding['quantity'] == 10
    assert holding['market_value'] == 1750.0 # 10 * 175
    assert holding['unrealized_pnl'] == 250.0 # 1750 - 1500