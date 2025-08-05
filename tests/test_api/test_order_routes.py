# tests/test_api/test_order_routes.py

from decimal import Decimal
from app.models.models import User, Portfolio, Account, Asset, AccountType

def test_place_buy_order_api_insufficient_funds(client, db):
    """
    GIVEN a user with insufficient funds
    WHEN a POST request is made to the /api/v1/orders endpoint to buy a stock
    THEN it should return a 400 Bad Request error
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash_account = Account(name="Cash", account_type=AccountType.CASH, balance=Decimal("100.00"), portfolio=portfolio)
    brokerage_account = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", last_price=Decimal("175.00"))
    db.session.add_all([user, portfolio, cash_account, brokerage_account, asset])
    db.session.commit()

    order_payload = {
        "account_id": brokerage_account.id,
        "ticker": "AAPL",
        "quantity": 10,
        "transaction_type": "BUY",
        "order_type": "MARKET"
    }

    # ACT
    response = client.post('/api/v1/orders', json=order_payload)
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 400
    assert 'error' in json_data
    assert "Insufficient funds" in json_data['error']

def test_place_buy_order_api_success(client, db):
    """
    GIVEN a user with sufficient funds
    WHEN a POST request is made to the /api/v1/orders endpoint to buy a stock
    THEN it should return a 201 Created status
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash_account = Account(name="Cash", account_type=AccountType.CASH, balance=Decimal("2000.00"), portfolio=portfolio)
    brokerage_account = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", last_price=Decimal("175.00"))
    db.session.add_all([user, portfolio, cash_account, brokerage_account, asset])
    db.session.commit()

    order_payload = {
        "account_id": brokerage_account.id,
        "ticker": "AAPL",
        "quantity": 10,
        "transaction_type": "BUY",
        "order_type": "MARKET"
    }

    # ACT
    response = client.post('/api/v1/orders', json=order_payload)
    
    # ASSERT
    assert response.status_code == 201