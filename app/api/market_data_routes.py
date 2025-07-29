from flask import Blueprint, jsonify
from ..services.market_data_service import MarketDataService

market_data_bp = Blueprint('market_data_bp', __name__)

@market_data_bp.route('/refresh', methods=['POST'])
def refresh_market_data_route():
    try:
        print("API triggered market data update...")
        MarketDataService.update_asset_prices()
        print("Market data update finished successfully via API.")
        return jsonify({"message": "Market data refresh completed successfully."}), 200
    except Exception as e:
        print(f"An error occurred during API-triggered refresh: {e}")
        return jsonify({"error": "An unexpected error occurred during the refresh process."}), 500