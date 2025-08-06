# tests/test_api/test_account_routes.py

from decimal import Decimal
from app.models.models import User, Portfolio, Account

def test_get_accounts_for_portfolio_api(client, db):
    """
    GIVEN a portfolio with a single account
    WHEN the GET /api/v1/accounts/portfolio/<id> endpoint is called
    THEN it should return a 200 OK with a list containing that one account
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    # FIX: The new logic assumes only one account per portfolio.
    account = Account(name="Primary Account", balance=Decimal("5000.00"), portfolio=portfolio)
    db.session.add_all([user, portfolio, account])
    db.session.commit()

    # ACT
    response = client.get(f'/api/v1/accounts/portfolio/{portfolio.id}')
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    assert isinstance(json_data, list)
    # FIX: Assert that only one account is returned.
    assert len(json_data) == 1
    assert json_data[0]['name'] == 'Primary Account'

def test_manage_funds_deposit_api(client, db):
    """
    GIVEN an account with an initial balance
    WHEN a POST request is made to the /api/v1/accounts/<id>/funds endpoint to DEPOSIT
    THEN it should return a 200 OK and the account balance should be updated
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    account = Account(name="Primary Account", balance=Decimal("1000.00"), portfolio=portfolio)
    db.session.add_all([user, portfolio, account])
    db.session.commit()

    payload = { "action": "DEPOSIT", "amount": 500.00 }

    # ACT
    response = client.post(f'/api/v1/accounts/{account.id}/funds', json=payload)
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    assert json_data['message'] == "Deposit successful."
    assert json_data['new_balance'] == 1500.00
    
    # Verify the change in the database
    updated_account = db.session.get(Account, account.id)
    assert updated_account.balance == Decimal("1500.00")