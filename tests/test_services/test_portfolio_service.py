# tests/test_services/test_portfolio_service.py

from decimal import Decimal
from app.services.portfolio_service import get_portfolio_summary, get_detailed_holdings
from app.models.models import User, Portfolio, Account, Asset, Holding, Transaction, AccountType, TransactionType
from datetime import date

def test_get_portfolio_summary_logic(db):
    """
    GIVEN a portfolio with various holdings and transactions
    WHEN the get_portfolio_summary service function is called
    THEN it should return a dictionary with accurately calculated metrics
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash = Account(name="Cash", account_type=AccountType.CASH, balance=Decimal("10000"), portfolio=portfolio)
    brokerage = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    
    aapl = Asset(ticker_symbol="AAPL", name="Apple", last_price=Decimal("175"), previous_close_price=Decimal("170"), sector="Tech")
    msft = Asset(ticker_symbol="MSFT", name="Microsoft", last_price=Decimal("300"), previous_close_price=Decimal("310"), sector="Tech")

    h_aapl = Holding(account=brokerage, asset=aapl, quantity=10, cost_basis=1500) # Market Value = 1750
    h_msft = Holding(account=brokerage, asset=msft, quantity=5, cost_basis=1600)  # Market Value = 1500

    # Cash Flow transactions
    t1 = Transaction(account=cash, transaction_type=TransactionType.DEPOSIT, total_amount=5000, transaction_date=date.today())
    t2 = Transaction(account=cash, transaction_type=TransactionType.WITHDRAWAL, total_amount=-2000, transaction_date=date.today())

    db.session.add_all([user, portfolio, cash, brokerage, aapl, msft, h_aapl, h_msft, t1, t2])
    db.session.commit()

    # ACT
    summary, error = get_portfolio_summary(portfolio.id)

    # ASSERT
    assert error is None
    # Net Worth = 10000 (cash) + 1750 (aapl) + 1500 (msft) = 13250
    assert summary['net_worth'] == 13250.0
    # Today's Change = (175-170)*10 + (300-310)*5 = 50 - 50 = 0
    assert summary['todays_change_amount'] == 0.0
    assert summary['cash_flow']['income'] == 5000.0
    assert summary['cash_flow']['spending'] == 2000.0
    assert summary['insights']['sector_allocation']['Tech'] == 100.0
    assert len(summary['insights']['top_gainers']) == 1
    assert summary['insights']['top_gainers'][0]['ticker'] == 'AAPL'
    assert len(summary['insights']['top_losers']) == 1
    assert summary['insights']['top_losers'][0]['ticker'] == 'MSFT'

def test_get_detailed_holdings_logic(db):
    """
    GIVEN a portfolio with holdings
    WHEN get_detailed_holdings is called
    THEN it should return a list of holdings with correct calculations
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    brokerage = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    aapl = Asset(ticker_symbol="AAPL", name="Apple", last_price=Decimal("175"))
    h_aapl = Holding(account=brokerage, asset=aapl, quantity=10, cost_basis=1500)
    db.session.add_all([user, portfolio, brokerage, aapl, h_aapl])
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