from flask import Blueprint, jsonify, request
from app.services.market_data_service import MarketDataService

market_data_bp = Blueprint('market_data_bp', __name__)

@market_data_bp.route('/search', methods=['GET'])
def search_assets_route():
    """Search for assets by ticker or name."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({"error": "Search query must be at least 2 characters long"}), 400
    
    results = MarketDataService.search_assets(query)
    return jsonify(results), 200

@market_data_bp.route('/asset/<string:ticker>', methods=['GET'])
def get_asset_details_route(ticker):
    """Get detailed information and historical data for a specific asset."""
    try:
        details = MarketDataService.get_asset_details(ticker)
        return jsonify(details), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@market_data_bp.route('/update-history/<int:asset_id>', methods=['POST'])
def update_history_route(asset_id):
    """Manually trigger an update of historical data for an asset."""
    # In a real app, this would be a protected admin endpoint
    MarketDataService.update_historical_data(asset_id)
    return jsonify({"message": "Historical data update initiated."}), 202
