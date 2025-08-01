# app/api/portfolio_routes.py

from flask import Blueprint, jsonify
from ..services.portfolio_service import get_portfolio_summary
from ..models.models import Account, Portfolio

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

@portfolio_bp.route('/<int:portfolio_id>/performance/movers', methods=['GET'])
def get_movers_route(portfolio_id):
    """
    Endpoint to get only the top 5 daily gainers and losers for a portfolio.
    """
    summary, error = get_portfolio_summary(portfolio_id)
    if error:
        return jsonify({"error": error}), 404
    
    movers = {
        "top_gainers": summary.get("insights", {}).get("top_gainers", []),
        "top_losers": summary.get("insights", {}).get("top_losers", [])
    }
    return jsonify(movers), 200

@portfolio_bp.route('/<int:portfolio_id>/allocation', methods=['GET'])
def get_allocation_route(portfolio_id):
    """
    Endpoint to get the portfolio's asset allocation by sector.
    """
    summary, error = get_portfolio_summary(portfolio_id)
    if error:
        return jsonify({"error": error}), 404

    allocation = summary.get("insights", {}).get("sector_allocation", {})
    return jsonify(allocation), 200

@portfolio_bp.route('/<int:portfolio_id>/accounts', methods=['GET'])
def get_accounts_route(portfolio_id):
    """Endpoint to retrieve all financial accounts for a specific portfolio."""
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        return jsonify({"error": "Portfolio not found"}), 404

    accounts_data = [{
        "id": acc.id,
        "name": acc.name,
        "account_type": acc.account_type,
        "balance": float(acc.balance) if acc.account_type == 'CASH' else float(sum(h.market_value for h in acc.holdings))
    } for acc in portfolio.accounts]
    
    return jsonify(accounts_data), 200