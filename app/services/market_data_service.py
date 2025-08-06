# app/services/market_data_service.py

import os
import yfinance as yf
from twelvedata import TDClient
from tiingo import TiingoClient
from datetime import datetime, timedelta
from app.models.models import db, Asset, HistoricalPrice, AssetType
from decimal import Decimal, InvalidOperation

# --- Configuration ---
TWELVE_DATA_API_KEY = os.environ.get('TWELVE_DATA_API_KEY')
TIINGO_API_KEY = os.environ.get('TIINGO_API_KEY')

td_client = TDClient(apikey=TWELVE_DATA_API_KEY) if TWELVE_DATA_API_KEY else None
tiingo_client = TiingoClient({'api_key': TIINGO_API_KEY}) if TIINGO_API_KEY else None

# --- Helper Functions ---
def safe_decimal(value, default=Decimal('0.0')):
    try:
        if value is None or str(value).lower() in ['none', 'nan', '']: return default
        return Decimal(str(value))
    except (InvalidOperation, ValueError): return default

def safe_int(value, default=0):
    try:
        if value is None or str(value).lower() in ['none', 'nan', '']: return default
        return int(value)
    except (ValueError, TypeError): return default

class MarketDataService:
    @staticmethod
    def _get_yfinance_data(ticker: str):
        """[Internal Helper] Fetches primary asset data from yfinance."""
        try:
            print(f"Using yfinance for primary data on {ticker}")
            y_ticker = yf.Ticker(ticker)
            info = y_ticker.info
            if info and 'longName' in info:
                return {
                    "name": info.get('longName'),
                    "last_price": safe_decimal(info.get('currentPrice')),
                    "previous_close": safe_decimal(info.get('previousClose')),
                    "market_cap": safe_int(info.get('marketCap')),
                    "sector": info.get('sector')
                }
        except Exception as e:
            print(f"yfinance failed for {ticker}: {e}")
        return None

    @staticmethod
    def find_or_create_asset(ticker: str):
        """Finds an asset by ticker or creates it using yfinance and Tiingo."""
        ticker = ticker.upper()
        asset = Asset.query.filter_by(ticker_symbol=ticker).first()
        if asset:
            return asset

        print(f"Asset '{ticker}' not in DB. Fetching from external APIs...")
        try:
            # 1. Fetch primary data from yfinance
            yfinance_data = MarketDataService._get_yfinance_data(ticker)
            if not yfinance_data:
                raise ValueError(f"Could not find valid data for {ticker} from yfinance.")

            # 2. Fetch supplemental metadata from Tiingo
            tiingo_meta = {}
            if tiingo_client:
                try:
                    tiingo_meta = tiingo_client.get_ticker_metadata(ticker)
                except Exception as e:
                    print(f"Could not fetch Tiingo metadata for {ticker}: {e}")
            
            # Create the asset with the best available data
            asset = Asset(
                ticker_symbol=ticker,
                name=yfinance_data['name'],
                asset_type=AssetType.STOCK,
                description=tiingo_meta.get('description'),
                exchange_code=tiingo_meta.get('exchangeCode'),
                last_price=yfinance_data['last_price'],
                previous_close_price=yfinance_data['previous_close'],
                market_cap=yfinance_data['market_cap'],
                sector=yfinance_data['sector'],
                price_updated_at=datetime.utcnow()
            )
            db.session.add(asset)
            db.session.commit()
            print(f"New asset '{asset.name}' created.")
            return asset
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Could not fetch or create asset for {ticker}: {e}")

    @staticmethod
    def update_asset_prices():
        """Fetches the latest market price for all assets, prioritizing yfinance."""
        print("Starting bulk asset price update...")
        assets_to_update = Asset.query.filter(Asset.asset_type.in_([AssetType.STOCK, AssetType.ETF])).all()
        if not assets_to_update:
            print("No assets to update.")
            return

        for asset in assets_to_update:
            price_data = MarketDataService._get_yfinance_data(asset.ticker_symbol)
            if price_data and price_data.get('last_price'):
                asset.last_price = price_data['last_price']
                asset.previous_close_price = price_data['previous_close']
                asset.price_updated_at = datetime.utcnow()
                print(f"Updated {asset.ticker_symbol}: Price={asset.last_price}")
            else:
                print(f"Could not update price for {asset.ticker_symbol}. Skipping.")
        
        db.session.commit()
        print("Database price update finished.")

    @staticmethod
    def get_asset_details(ticker: str):
        """Gets detailed fundamental and historical data for an asset."""
        asset = MarketDataService.find_or_create_asset(ticker)
        
        MarketDataService.update_historical_data(asset.id)

        historical_data = HistoricalPrice.query.filter_by(asset_id=asset.id).order_by(HistoricalPrice.price_date.asc()).all()
        
        return {
            "asset_id": asset.id,
            "ticker_symbol": asset.ticker_symbol,
            "name": asset.name,
            "description": asset.description,
            "exchange": asset.exchange_code,
            "last_price": float(asset.last_price) if asset.last_price is not None else 0.0,
            "previous_close_price": float(asset.previous_close_price) if asset.previous_close_price is not None else 0.0,
            "market_cap": asset.market_cap,
            "sector": asset.sector,
            "historical_data": [{"date": h.price_date.isoformat(), "close": float(h.close_price)} for h in historical_data]
        }

    @staticmethod
    def update_historical_data(asset_id: int):
        """Fetches and stores historical data for a given asset using Twelve Data."""
        asset = Asset.query.get(asset_id)
        if not asset or not td_client:
            return

        print(f"Updating historical data for {asset.ticker_symbol}...")
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            ts = td_client.time_series(
                symbol=asset.ticker_symbol,
                interval="1day",
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            ).as_json()

            for row in ts:
                price_date = datetime.strptime(row['datetime'], '%Y-%m-%d').date()
                record_exists = HistoricalPrice.query.filter_by(asset_id=asset.id, price_date=price_date).first()
                if not record_exists:
                    new_price = HistoricalPrice(
                        asset_id=asset.id,
                        price_date=price_date,
                        open_price=safe_decimal(row.get('open')),
                        high_price=safe_decimal(row.get('high')),
                        low_price=safe_decimal(row.get('low')),
                        close_price=safe_decimal(row.get('close')),
                        volume=safe_int(row.get('volume'))
                    )
                    db.session.add(new_price)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to update historical data for {asset.ticker_symbol}: {e}")

    @staticmethod
    def search_assets(query: str):
        """Searches for assets by ticker or name in the local database."""
        search = f"%{query}%"
        assets = Asset.query.filter(
            (Asset.ticker_symbol.ilike(search)) | (Asset.name.ilike(search))
        ).limit(10).all()
        return [{"ticker": a.ticker_symbol, "name": a.name} for a in assets]