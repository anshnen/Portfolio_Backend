from flask import Blueprint, jsonify
from ..services.portfolio_service import get_portfolio_summary
from ..models.models import Account

portfolio_bp = Blueprint('portfolio_bp', __name__)

@portfolio_bp.route('/<int:portfolio_id>/summary', methods=['GET'])
def get_summary_route(portfolio_id):
    """
    Endpoint to get a full summary of a portfolio.
    This is the main endpoint for the dashboard UI.
    """
    summary, error = get_portfolio_summary(portfolio_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(summary), 200

@portfolio_bp.route('/accounts', methods=['GET'])
def get_accounts_route():
    """Endpoint to retrieve all financial accounts."""
    accounts = Account.query.all()
    accounts_data = [{
        "id": acc.id,
        "name": acc.name,
        "institution": acc.institution,
        "account_type": acc.account_type,
        "balance": float(acc.balance)
    } for acc in accounts]
    return jsonify(accounts_data), 200