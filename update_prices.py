import os
from app import create_app
from app.services.market_data_service import MarketDataService

if __name__ == '__main__':
    config_name = os.getenv('FLASK_CONFIG', 'development')
    app = create_app(config_name)

    with app.app_context():
        print("Starting market data update...")
        MarketDataService.update_asset_prices()
        print("Market data update finished.")