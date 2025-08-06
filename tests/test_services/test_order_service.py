# tests/test_services/test_order_service.py

import pytest
from decimal import Decimal
from app.services.order_service import OrderService
from app.models.models import User, Portfolio, Account, Asset, Holding, TransactionStatus, AccountType, AssetType
from tests.data.mock_api_data import MOCK_AAPL_DATA

def test_place_market_buy_order_success(db):
    """
    GIVEN a user with sufficient funds
    WHEN a valid MARKET BUY order is placed via the OrderService
    THEN a new holding should be created and the cash balance should be reduced correctly
    """
    # ARRANGE: Set up the initial state in the test database
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash_account = Account(name="Cash", account_type=AccountType.CASH, balance=Decimal("10000"), portfolio=portfolio)
    brokerage_account = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    # FIX: Added the required 'asset_type' field.
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK, last_price=MOCK_AAPL_DATA['last_price'])
    db.session.add_all([user, portfolio, cash_account, brokerage_account, asset])
    db.session.commit()

    order_data = {
        "account_id": brokerage_account.id,
        "ticker": "AAPL",
        "quantity": 10,
        "transaction_type": "BUY",
        "order_type": "MARKET"
    }

    # ACT: Call the service function being tested
    transaction = OrderService.place_order(user_id=user.id, order_data=order_data)
    
    # ASSERT: Verify the outcome
    holding = Holding.query.filter_by(account_id=brokerage_account.id, asset_id=asset.id).first()
    assert holding is not None
    assert holding.quantity == 10
    # Verify cash is reduced by the value of the stock PLUS the commission fee
    assert cash_account.balance == Decimal("10000") - (Decimal("10") * MOCK_AAPL_DATA['last_price']) - OrderService.BROKERAGE_FEE
    assert transaction.status == TransactionStatus.COMPLETED
    assert transaction.realized_pnl is None # P&L is only for sells

def test_place_market_sell_order_success(db):
    """
    GIVEN a user with an existing holding
    WHEN a valid MARKET SELL order is placed
    THEN the holding quantity should decrease, cash balance should increase, and P&L calculated
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash_account = Account(name="Cash", account_type=AccountType.CASH, balance=Decimal("10000"), portfolio=portfolio)
    brokerage_account = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    # FIX: Added the required 'asset_type' field.
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK, last_price=Decimal("200.00"))
    holding = Holding(account=brokerage_account, asset=asset, quantity=50, cost_basis=Decimal("7500")) # Avg price = 150
    db.session.add_all([user, portfolio, cash_account, brokerage_account, asset, holding])
    db.session.commit()

    order_data = { "account_id": brokerage_account.id, "ticker": "AAPL", "quantity": 20, "transaction_type": "SELL", "order_type": "MARKET" }

    # ACT
    transaction = OrderService.place_order(user_id=user.id, order_data=order_data)

    # ASSERT
    assert holding.quantity == 30 # 50 - 20
    assert cash_account.balance == Decimal("10000") + (Decimal("20") * Decimal("200.00")) - OrderService.BROKERAGE_FEE
    assert transaction.status == TransactionStatus.COMPLETED
    # Realized P&L = (20 shares * $200 sell price) - (20 shares * $150 avg cost) = 4000 - 3000 = 1000
    assert transaction.realized_pnl == Decimal("1000.00")

def test_place_buy_order_insufficient_funds(db):
    """
    GIVEN a user with insufficient funds
    WHEN a BUY order is placed
    THEN a ValueError should be raised
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash_account = Account(name="Cash", account_type=AccountType.CASH, balance=Decimal("100.00"), portfolio=portfolio)
    brokerage_account = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    # FIX: Added the required 'asset_type' field.
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK, last_price=MOCK_AAPL_DATA['last_price'])
    db.session.add_all([user, portfolio, cash_account, brokerage_account, asset])
    db.session.commit()

    order_data = { "account_id": brokerage_account.id, "ticker": "AAPL", "quantity": 10, "transaction_type": "BUY", "order_type": "MARKET" }

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Insufficient funds"):
        OrderService.place_order(user_id=user.id, order_data=order_data)

def test_place_limit_buy_order(db):
    """
    GIVEN a user and account
    WHEN a LIMIT BUY order is placed
    THEN a new transaction should be created with a 'PENDING' status
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    brokerage_account = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    # FIX: Added the required 'asset_type' field.
    asset = Asset(ticker_symbol="GOOGL", name="Alphabet Inc.", asset_type=AssetType.STOCK, last_price=Decimal("170.00"))
    db.session.add_all([user, portfolio, brokerage_account, asset])
    db.session.commit()

    order_data = {
        "account_id": brokerage_account.id,
        "ticker": "GOOGL",
        "quantity": 5,
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "trigger_price": 150.00
    }

    # ACT
    transaction = OrderService.place_order(user_id=user.id, order_data=order_data)

    # ASSERT
    assert transaction is not None
    assert transaction.status == TransactionStatus.PENDING
    assert transaction.order_type == 'LIMIT'
    assert transaction.trigger_price == Decimal("150.00")