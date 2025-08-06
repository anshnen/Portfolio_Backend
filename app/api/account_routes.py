# app/api/account_routes.py

from flask import Blueprint, jsonify, request
from app.models.models import db, Account, Transaction, Portfolio, TransactionType
from decimal import Decimal
from datetime import date

account_bp = Blueprint('account_bp', __name__)

@account_bp.route('/', methods=['POST'])
def create_account():
    """Creates a new financial account for a portfolio."""
    data = request.get_json()
    # Simplified validation for a single-account model
    if not data or not all(k in data for k in ['portfolio_id', 'name']):
        return jsonify({"error": "Missing required fields: portfolio_id, name"}), 400

    portfolio = db.session.get(Portfolio, data['portfolio_id'])
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404
    
    # Prevent creating more than one account per portfolio in this simplified model
    if portfolio.accounts:
        return jsonify({"error": "A primary account already exists for this portfolio."}), 400

    new_account = Account(
        portfolio_id=data['portfolio_id'],
        name=data['name'],
        balance=Decimal(str(data.get('balance', '0.00')))
    )
    db.session.add(new_account)
    db.session.commit()

    return jsonify({
        "message": "Account created successfully.",
        "account": {
            "id": new_account.id,
            "name": new_account.name,
            "balance": float(new_account.balance)
        }
    }), 201

@account_bp.route('/portfolio/<int:portfolio_id>', methods=['GET'])
def get_accounts_for_portfolio(portfolio_id):
    """Retrieves the primary financial account for a specific portfolio."""
    account = Account.query.filter_by(portfolio_id=portfolio_id).first()
    if not account:
        return jsonify([]), 200 # Return empty list if no account exists yet

    account_data = [{
        "id": account.id,
        "name": account.name,
        "balance": float(account.balance + account.holdings_market_value)
    }]
    return jsonify(account_data), 200


@account_bp.route('/<int:account_id>/funds', methods=['POST'])
def manage_funds(account_id):
    """Endpoint for depositing or withdrawing funds from the primary account."""
    data = request.get_json()
    if not data or 'action' not in data or 'amount' not in data:
        return jsonify({"error": "Missing 'action' (DEPOSIT/WITHDRAWAL) or 'amount'"}), 400

    account = db.session.get(Account, account_id)
    if not account:
        return jsonify({"error": "Account not found"}), 404

    action = data['action'].upper()
    amount = Decimal(str(data['amount']))

    if amount <= 0:
        return jsonify({"error": "Amount must be positive."}), 400

    if action == 'DEPOSIT':
        account.balance += amount
        transaction_type = TransactionType.DEPOSIT
        total_amount = amount
    elif action == 'WITHDRAWAL':
        if account.balance < amount:
            return jsonify({"error": "Insufficient funds for withdrawal."}), 400
        account.balance -= amount
        transaction_type = TransactionType.WITHDRAWAL
        total_amount = -amount
    else:
        return jsonify({"error": "Invalid action. Must be 'DEPOSIT' or 'WITHDRAWAL'."}), 400

    transaction = Transaction(
        account_id=account.id,
        transaction_type=transaction_type,
        total_amount=total_amount,
        transaction_date=date.today(),
        description=f"User initiated {action.lower()}."
    )
    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "message": f"{action.capitalize()} successful.",
        "new_balance": float(account.balance)
    }), 200