from flask import Blueprint, jsonify, request
from app.models.models import db, Account, Transaction, Portfolio
from decimal import Decimal
from datetime import date

account_bp = Blueprint('account_bp', __name__)

@account_bp.route('/', methods=['POST'])
def create_account():
    """Creates a new financial account for a portfolio."""
    data = request.get_json()
    if not data or not all(k in data for k in ['portfolio_id', 'name', 'account_type']):
        return jsonify({"error": "Missing required fields: portfolio_id, name, account_type"}), 400

    portfolio = Portfolio.query.get(data['portfolio_id'])
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404

    new_account = Account(
        portfolio_id=data['portfolio_id'],
        name=data['name'],
        account_type=data['account_type'].upper(),
        institution=data.get('institution'),
        balance=Decimal(str(data.get('balance', '0.00')))
    )
    db.session.add(new_account)
    db.session.commit()

    return jsonify({
        "message": "Account created successfully.",
        "account": {
            "id": new_account.id,
            "name": new_account.name,
            "account_type": new_account.account_type,
            "balance": float(new_account.balance)
        }
    }), 201

@account_bp.route('/portfolio/<int:portfolio_id>', methods=['GET'])
def get_accounts_for_portfolio(portfolio_id):
    """Retrieves all financial accounts for a specific portfolio."""
    accounts = Account.query.filter_by(portfolio_id=portfolio_id).all()
    accounts_data = [{
        "id": acc.id,
        "name": acc.name,
        "account_type": acc.account_type.value,
        "balance": float(acc.balance)
    } for acc in accounts]
    return jsonify(accounts_data), 200


@account_bp.route('/<int:account_id>/funds', methods=['POST'])
def manage_funds(account_id):
    """Endpoint for depositing or withdrawing funds from a cash account."""
    data = request.get_json()
    if not data or 'action' not in data or 'amount' not in data:
        return jsonify({"error": "Missing 'action' (DEPOSIT/WITHDRAWAL) or 'amount'"}), 400

    account = Account.query.get(account_id)
    if not account or account.account_type.value != 'CASH': # Compare with enum's value
        return jsonify({"error": "Funds can only be managed in a CASH account."}), 400

    action = data['action'].upper()
    amount = Decimal(str(data['amount']))

    if amount <= 0:
        return jsonify({"error": "Amount must be positive."}), 400

    if action == 'DEPOSIT':
        account.balance += amount
        transaction_type = 'DEPOSIT'
        total_amount = amount
    elif action == 'WITHDRAWAL':
        if account.balance < amount:
            return jsonify({"error": "Insufficient funds for withdrawal."}), 400
        account.balance -= amount
        transaction_type = 'WITHDRAWAL'
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