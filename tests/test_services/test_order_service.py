# tests/test_services/test_order_service.py

import pytest
from decimal import Decimal
from app.services.order_service import OrderService
from app.models.models import User, Portfolio, Account, Asset, Holding, TransactionStatus, AssetType
from tests.data.mock_api_data import MOCK_AAPL_DATA

def test_place_market_buy_order_success(db):
    """
    GIVEN a user with a single account with sufficient funds
    WHEN a valid MARKET BUY order is placed
    THEN a new holding should be created and the account balance should be reduced correctly
    """
    # ARRANGE: Set up the initial state with a single account
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    account = Account(name="Primary Account", balance=Decimal("10000"), portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK, last_price=MOCK_AAPL_DATA['last_price'])
    db.session.add_all([user, portfolio, account, asset])
    db.session.commit()

    order_data = {
        "account_id": account.id,
        "ticker": "AAPL",
        "quantity": 10,
        "transaction_type": "BUY",
        "order_type": "MARKET"
    }

    # ACT
    transaction = OrderService.place_order(user_id=user.id, order_data=order_data)
    
    # ASSERT
    holding = Holding.query.filter_by(account_id=account.id, asset_id=asset.id).first()
    assert holding is not None
    assert holding.quantity == 10
    # Verify balance is reduced by the value of the stock PLUS the commission fee
    assert account.balance == Decimal("10000") - (Decimal("10") * MOCK_AAPL_DATA['last_price']) - OrderService.BROKERAGE_FEE
    assert transaction.status == TransactionStatus.COMPLETED

def test_place_market_sell_order_success(db):
    """
    GIVEN a user with an existing holding in their single account
    WHEN a valid MARKET SELL order is placed
    THEN the holding quantity should decrease, account balance should increase, and P&L calculated
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    account = Account(name="Primary Account", balance=Decimal("10000"), portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK, last_price=Decimal("200.00"))
    holding = Holding(account=account, asset=asset, quantity=50, cost_basis=Decimal("7500")) # Avg price = 150
    db.session.add_all([user, portfolio, account, asset, holding])
    db.session.commit()

    order_data = { "account_id": account.id, "ticker": "AAPL", "quantity": 20, "transaction_type": "SELL", "order_type": "MARKET" }

    # ACT
    transaction = OrderService.place_order(user_id=user.id, order_data=order_data)

    # ASSERT
    assert holding.quantity == 30 # 50 - 20
    assert account.balance == Decimal("10000") + (Decimal("20") * Decimal("200.00")) - OrderService.BROKERAGE_FEE
    assert transaction.status == TransactionStatus.COMPLETED
    assert transaction.realized_pnl == Decimal("1000.00")

def test_place_buy_order_insufficient_funds(db):
    """
    GIVEN a user with a single account with insufficient funds
    WHEN a BUY order is placed
    THEN a ValueError should be raised
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    account = Account(name="Primary Account", balance=Decimal("100.00"), portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK, last_price=MOCK_AAPL_DATA['last_price'])
    db.session.add_all([user, portfolio, account, asset])
    db.session.commit()

    order_data = { "account_id": account.id, "ticker": "AAPL", "quantity": 10, "transaction_type": "BUY", "order_type": "MARKET" }

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Insufficient funds"):
        OrderService.place_order(user_id=user.id, order_data=order_data)

def test_place_limit_buy_order(db):
    """
    GIVEN a user and their single account
    WHEN a LIMIT BUY order is placed
    THEN a new transaction should be created with a 'PENDING' status
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    account = Account(name="Primary Account", portfolio=portfolio)
    asset = Asset(ticker_symbol="GOOGL", name="Alphabet Inc.", asset_type=AssetType.STOCK, last_price=Decimal("170.00"))
    db.session.add_all([user, portfolio, account, asset])
    db.session.commit()

    order_data = {
        "account_id": account.id,
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