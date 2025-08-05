# tests/test_api/test_account_routes.py

from decimal import Decimal
from app.models.models import User, Portfolio, Account, AccountType

def test_get_accounts_for_portfolio_api(client, db):
    """
    GIVEN a portfolio with multiple accounts
    WHEN the GET /api/v1/accounts/portfolio/<id> endpoint is called
    THEN it should return a 200 OK with a list of the correct accounts
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash_account = Account(name="Cash", account_type=AccountType.CASH, balance=Decimal("5000.00"), portfolio=portfolio)
    brokerage_account = Account(name="Brokerage", account_type=AccountType.INVESTMENT, portfolio=portfolio)
    db.session.add_all([user, portfolio, cash_account, brokerage_account])
    db.session.commit()

    # ACT
    response = client.get(f'/api/v1/accounts/portfolio/{portfolio.id}')
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    assert isinstance(json_data, list)
    assert len(json_data) == 2
    assert json_data[0]['name'] == 'Cash'
    assert json_data[1]['name'] == 'Brokerage'

def test_manage_funds_deposit_api(client, db):
    """
    GIVEN a cash account with an initial balance
    WHEN a POST request is made to the /api/v1/accounts/<id>/funds endpoint to DEPOSIT
    THEN it should return a 200 OK and the account balance should be updated
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    cash_account = Account(name="Cash", account_type=AccountType.CASH, balance=Decimal("1000.00"), portfolio=portfolio)
    db.session.add_all([user, portfolio, cash_account])
    db.session.commit()

    payload = { "action": "DEPOSIT", "amount": 500.00 }

    # ACT
    response = client.post(f'/api/v1/accounts/{cash_account.id}/funds', json=payload)
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    assert json_data['message'] == "Deposit successful."
    assert json_data['new_balance'] == 1500.00
    
    # Verify the change in the database
    updated_account = Account.query.get(cash_account.id)
    assert updated_account.balance == Decimal("1500.00")