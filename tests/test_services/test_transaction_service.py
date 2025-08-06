# tests/test_services/test_transaction_service.py

from decimal import Decimal
from datetime import date
from app.services.transaction_service import add_transaction, get_transactions_by_account
from app.models.models import User, Portfolio, Account, Transaction, TransactionType

def test_add_deposit_transaction(db):
    """
    GIVEN a user with a single account
    WHEN a DEPOSIT transaction is added via the service
    THEN the account balance should increase by the correct amount
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    # FIX: Create a single account without the removed 'account_type'
    account = Account(name="Primary Account", balance=Decimal("1000.00"), portfolio=portfolio)
    db.session.add_all([user, portfolio, account])
    db.session.commit()

    transaction_data = {
        "account_id": account.id,
        "transaction_type": "DEPOSIT",
        "total_amount": "500.00",
        "transaction_date": date.today().strftime('%Y-%m-%d'),
        "description": "Paycheck"
    }

    # ACT
    new_transaction = add_transaction(transaction_data)

    # ASSERT
    assert account.balance == Decimal("1500.00")
    assert new_transaction.transaction_type == TransactionType.DEPOSIT
    assert new_transaction.description == "Paycheck"

def test_get_transactions_by_account(db):
    """
    GIVEN an account with multiple transactions
    WHEN get_transactions_by_account is called
    THEN it should return a correctly formatted list of those transactions
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    # FIX: Create a single account without the removed 'account_type'
    account = Account(name="Primary Account", portfolio=portfolio)
    t1 = Transaction(account=account, transaction_type=TransactionType.DEPOSIT, total_amount=100, transaction_date=date.today())
    t2 = Transaction(account=account, transaction_type=TransactionType.WITHDRAWAL, total_amount=-50, transaction_date=date.today())
    db.session.add_all([user, portfolio, account, t1, t2])
    db.session.commit()

    # ACT
    transactions_list = get_transactions_by_account(account.id)

    # ASSERT
    assert isinstance(transactions_list, list)
    assert len(transactions_list) == 2
    
    # This robust assertion correctly checks for the presence of both amounts.
    amounts = {t['total_amount'] for t in transactions_list}
    assert 100.0 in amounts
    assert -50.0 in amounts