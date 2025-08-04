# update_prices.py

import os
from app import create_app
from app.services.market_data_service import MarketDataService
from app.models.models import Asset, AssetType

def run_full_update():
    """
    Initializes the Flask app and runs a comprehensive market data update.
    - Updates the latest prices for all assets.
    - Updates fundamental & technical data (market cap, P/E, etc.).
    - Updates the historical price data for all assets.
    This script is intended to be run on a schedule (e.g., daily).
    """
    config_name = os.getenv('FLASK_CONFIG', 'development')
    app = create_app(config_name)

    with app.app_context():
        print("--- Starting Comprehensive Market Data Update ---")

        # 1. Update latest prices
        print("\nStep 1: Updating latest asset prices...")
        MarketDataService.update_asset_prices()
        print("Latest price update finished.")

        # 2. Update fundamental and technical data
        print("\nStep 2: Updating fundamental and technical data (Market Cap, P/E, etc.)...")
        MarketDataService.update_all_asset_details()
        print("Fundamental and technical data update finished.")

        # 3. Update historical price data for all relevant assets
        print("\nStep 3: Updating historical price data for all assets...")
        assets_for_history = Asset.query.filter(Asset.asset_type.in_([AssetType.STOCK, AssetType.ETF, AssetType.INDEX])).all()
        if not assets_for_history:
            print("No assets found requiring historical data updates.")
        else:
            for asset in assets_for_history:
                try:
                    MarketDataService.update_historical_data(asset.id)
                except Exception as e:
                    print(f"Could not update historical data for {asset.ticker_symbol}: {e}")
        
        print("Historical data update finished.")
        print("\n--- Comprehensive Market Data Update Complete ---")

if __name__ == '__main__':
    run_full_update()