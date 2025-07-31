import os
from app import create_app
from app.services.market_data_service import MarketDataService

def run_update():
    """
    Initializes the Flask app and runs the market data update service.
    This script is intended to be run separately after seeding or on a schedule.
    """
    config_name = os.getenv('FLASK_CONFIG', 'development')
    app = create_app(config_name)

    with app.app_context():
        print("Starting market data update...")
        MarketDataService.update_asset_prices()
        print("Market data update finished.")

if __name__ == '__main__':
    run_update()