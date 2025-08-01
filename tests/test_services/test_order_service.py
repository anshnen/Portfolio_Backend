# tests/test_services/test_order_service.py

import pytest
from decimal import Decimal
from app.services.order_service import OrderService
from app.models.models import User, Portfolio, Account, Asset, Holding
from tests.data.mock_api_data import MOCK_AAPL_DATA

def test_place_buy_order_success(db):
    """
    GIVEN a user, portfolio, cash account with sufficient funds, and an asset
    WHEN a valid MARKET BUY order is placed
    THEN a new holding should be created, and the cash balance should be reduced correctly
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash_account = Account(name="Cash", account_type="CASH", balance=Decimal("10000"), portfolio=portfolio)
    brokerage_account = Account(name="Brokerage", account_type="INVESTMENT", portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", last_price=MOCK_AAPL_DATA['last_price'])
    db.session.add_all([user, portfolio, cash_account, brokerage_account, asset])
    db.session.commit()

    order_data = {
        "account_id": brokerage_account.id,
        "ticker": "AAPL",
        "quantity": 10,
        "transaction_type": "BUY",
        "order_type": "MARKET"
    }

    # ACT
    transaction = OrderService.place_order(user_id=user.id, order_data=order_data)
    
    # ASSERT
    holding = Holding.query.filter_by(account_id=brokerage_account.id, asset_id=asset.id).first()
    assert holding is not None
    assert holding.quantity == 10
    assert cash_account.balance == Decimal("10000") - (Decimal("10") * MOCK_AAPL_DATA['last_price']) - OrderService.BROKERAGE_FEE
    assert transaction.status == 'COMPLETED'
    assert transaction.realized_pnl is None # P&L is only for sells

def test_place_sell_order_insufficient_shares(db):
    """
    GIVEN a user with no holdings of a stock
    WHEN a SELL order is placed for that stock
    THEN a ValueError should be raised
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    brokerage_account = Account(name="Brokerage", account_type="INVESTMENT", portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", last_price=MOCK_AAPL_DATA['last_price'])
    db.session.add_all([user, portfolio, brokerage_account, asset])
    db.session.commit()

    order_data = {
        "account_id": brokerage_account.id,
        "ticker": "AAPL",
        "quantity": 10,
        "transaction_type": "SELL",
        "order_type": "MARKET"
    }

    # ACT & ASSERT
    with pytest.raises(ValueError, match="Insufficient shares to sell"):
        OrderService.place_order(user_id=user.id, order_data=order_data)