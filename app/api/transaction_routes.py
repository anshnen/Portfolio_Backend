# app/api/transaction_routes.py

from flask import Blueprint, jsonify, request
from ..services.transaction_service import add_transaction, get_transactions_by_account, update_transaction

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
        # Corrected status code from 50 to 500
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    
@transaction_bp.route('/<int:transaction_id>', methods=['PUT'])
def update_transaction_route(transaction_id):
    """
    Endpoint to update an existing transaction.
    Note: This is generally not recommended for financial ledgers.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400

    try:
        transaction = update_transaction(transaction_id, data)
        return jsonify({"message": "Transaction updated successfully", "transactionId": transaction.id}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404 # Use 404 if transaction not found
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500