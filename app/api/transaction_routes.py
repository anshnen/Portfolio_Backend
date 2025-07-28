from flask import Blueprint, jsonify, request
from ..services.transaction_service import add_transaction, get_transactions_by_account

transaction_bp = Blueprint('transaction_bp', __name__)

@transaction_bp.route('/', methods=['POST'])
def create_transaction_route():
    """
    Endpoint to add a new transaction. This is a critical endpoint
    that updates account balances and holdings.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    try:
        transaction = add_transaction(data)
        return jsonify({"message": "Transaction added successfully", "transactionId": transaction.id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@transaction_bp.route('/account/<int:account_id>', methods=['GET'])
def get_transactions_route(account_id):
    """Endpoint to get all transactions for a specific account."""
    try:
        transactions = get_transactions_by_account(account_id)
        return jsonify(transactions), 200
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500