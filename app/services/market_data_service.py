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

td_client = TDClient(apikey=TWELVE_DATA_API_KEY) if TWELVE_DATA_API_KEY and TWELVE_DATA_API_KEY != 'YOUR_TWELVE_DATA_KEY' else None
tiingo_client = TiingoClient({'api_key': TIINGO_API_KEY}) if TIINGO_API_KEY and TIINGO_API_KEY != 'YOUR_TIINGO_KEY' else None

# --- Helper Functions ---
def safe_decimal(value, default=Decimal('0.0')):
    """Safely converts a value to a Decimal, returning a default on failure."""
    try:
        if value is None or str(value).lower() in ['none', 'nan', '']: return default
        return Decimal(str(value))
    except (InvalidOperation, ValueError): return default

def safe_int(value, default=0):
    """Safely converts a value to an integer, returning a default on failure."""
    try:
        if value is None or str(value).lower() in ['none', 'nan', '']: return default
        return int(float(value))
    except (ValueError, TypeError): return default

class MarketDataService:
    @staticmethod
    def _get_yfinance_data(ticker: str):
        """[Internal Helper] Fetches comprehensive asset data from yfinance."""
        try:
            print(f"Primary source: Attempting yfinance for {ticker}")
            y_ticker = yf.Ticker(ticker)
            info = y_ticker.info
            
            if info and info.get('longName'):
                list_date_ms = info.get('firstTradeDateMilliseconds')
                return {
                    "name": info.get('longName'),
                    "description": info.get('longBusinessSummary'),
                    "exchange_code": info.get('exchange'),
                    "list_date": datetime.fromtimestamp(list_date_ms / 1000).date() if list_date_ms else None,
                    "last_price": safe_decimal(info.get('currentPrice') or info.get('regularMarketPrice')),
                    "previous_close": safe_decimal(info.get('previousClose') or info.get('regularMarketPreviousClose')),
                    "currency": info.get('financialCurrency', 'USD')
                }
        except Exception as e:
            print(f"yfinance failed for {ticker}: {e}")
        return None

    @staticmethod
    def find_or_create_asset(ticker: str):
        """Finds an asset by ticker or creates it using a tiered fallback system."""
        ticker = ticker.upper()
        asset = Asset.query.filter_by(ticker_symbol=ticker).first()
        if asset:
            return asset

        print(f"Asset '{ticker}' not in DB. Fetching from external APIs...")
        
        # 1. Primary source: yfinance
        asset_data = MarketDataService._get_yfinance_data(ticker)

        # 2. Fallback sources if primary fails
        if not asset_data:
            print(f"yfinance failed for {ticker}. Trying fallbacks.")
            asset_data = {}
            try:
                # Price from Twelve Data
                if td_client:
                    print(f"Fallback: Attempting Twelve Data for price on {ticker}")
                    quote = td_client.quote(symbol=ticker).as_json()
                    asset_data['last_price'] = safe_decimal(quote.get('close'))
                    asset_data['previous_close'] = safe_decimal(quote.get('previous_close'))
                    asset_data['name'] = quote.get('name') # Get name from here too
                
                # Metadata from Tiingo
                if tiingo_client:
                    print(f"Fallback: Attempting Tiingo for metadata on {ticker}")
                    meta = tiingo_client.get_ticker_metadata(ticker)
                    # Don't overwrite name if already present
                    if 'name' not in asset_data: asset_data['name'] = meta.get('name')
                    asset_data['description'] = meta.get('description')
                    asset_data['exchange_code'] = meta.get('exchangeCode')
                    if meta.get('startDate'):
                        asset_data['list_date'] = datetime.strptime(meta['startDate'], '%Y-%m-%d').date()
            except Exception as e:
                db.session.rollback()
                raise ValueError(f"All fallback API calls failed for {ticker}: {e}")

        # 3. Create asset if we have minimum data (name and price)
        if not asset_data or not asset_data.get('name') or not asset_data.get('last_price'):
            raise ValueError(f"Could not find valid data for {ticker} from any source.")
            
        try:
            asset = Asset(
                ticker_symbol=ticker,
                name=asset_data['name'],
                asset_type=AssetType.STOCK,
                description=asset_data.get('description'),
                exchange_code=asset_data.get('exchange_code'),
                list_date=asset_data.get('list_date'),
                last_price=asset_data['last_price'],
                previous_close_price=asset_data.get('previous_close'),
                currency=asset_data.get('currency', 'USD'),
                price_updated_at=datetime.utcnow()
            )
            db.session.add(asset)
            db.session.commit()
            print(f"New asset '{asset.name}' created.")
            return asset
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to commit new asset {ticker} to DB: {e}")

    @staticmethod
    def update_asset_prices():
        """Fetches the latest market price for all assets, with fallbacks."""
        print("Starting bulk asset price update...")
        assets = Asset.query.filter(Asset.asset_type.in_([AssetType.STOCK, AssetType.ETF])).all()
        if not assets:
            print("No assets to update."); return

        for asset in assets:
            # 1. Try yfinance
            price_data = MarketDataService._get_yfinance_data(asset.ticker_symbol)
            
            # 2. Fallback to Twelve Data if yfinance fails
            if not price_data or not price_data.get('last_price'):
                if td_client:
                    try:
                        print(f"Price fallback: Twelve Data for {asset.ticker_symbol}")
                        quote = td_client.quote(symbol=asset.ticker_symbol).as_json()
                        price_data = {
                            'last_price': safe_decimal(quote.get('close')),
                            'previous_close': safe_decimal(quote.get('previous_close'))
                        }
                    except Exception as e:
                        print(f"Twelve Data price fallback failed for {asset.ticker_symbol}: {e}")

            # 3. Update if data was found from any source
            if price_data and price_data.get('last_price'):
                asset.last_price = price_data['last_price']
                asset.previous_close_price = price_data['previous_close']
                asset.price_updated_at = datetime.utcnow()
                print(f"Updated {asset.ticker_symbol}: Price={asset.last_price}")
            else:
                print(f"Could not update price for {asset.ticker_symbol} from any source.")
        
        db.session.commit()
        print("Database price update finished.")

    @staticmethod
    def get_asset_details(ticker: str):
        """Gets detailed and historical data for an asset."""
        asset = MarketDataService.find_or_create_asset(ticker)
        MarketDataService.update_all_asset_details(asset.id)
        MarketDataService.update_historical_data(asset.id)
        asset = db.session.get(Asset, asset.id)
        historical_data = HistoricalPrice.query.filter_by(asset_id=asset.id).order_by(HistoricalPrice.price_date.asc()).all()
        return {
            "asset_id": asset.id, "ticker_symbol": asset.ticker_symbol, "name": asset.name,
            "description": asset.description, "exchange": asset.exchange_code,
            "list_date": asset.list_date.isoformat() if asset.list_date else None,
            "last_price": float(asset.last_price) if asset.last_price is not None else 0.0,
            "previous_close_price": float(asset.previous_close_price) if asset.previous_close_price is not None else 0.0,
            "currency": asset.currency,
            "historical_data": [{"date": h.price_date.isoformat(), "close": float(h.close_price)} for h in historical_data]
        }

    @staticmethod
    def update_historical_data(asset_id: int):
        """Fetches and stores historical data for an asset, with fallbacks."""
        asset = db.session.get(Asset, asset_id)
        if not asset: return

        print(f"Updating historical data for {asset.ticker_symbol}...")
        try:
            # 1. Primary: yfinance
            print(f"Hist. data: Trying yfinance for {asset.ticker_symbol}")
            y_ticker = yf.Ticker(asset.ticker_symbol)
            hist_df = y_ticker.history(period="1y", interval="1d")
            if hist_df.empty: raise ValueError("yfinance returned no historical data.")
            for price_date, row in hist_df.iterrows():
                price_date_obj = price_date.date()
                if not HistoricalPrice.query.filter_by(asset_id=asset.id, price_date=price_date_obj).first():
                    db.session.add(HistoricalPrice(
                        asset_id=asset.id, price_date=price_date_obj,
                        open_price=safe_decimal(row.get('Open')), high_price=safe_decimal(row.get('High')),
                        low_price=safe_decimal(row.get('Low')), close_price=safe_decimal(row.get('Close')),
                        volume=safe_int(row.get('Volume'))
                    ))
            db.session.commit()
        except Exception as e_yf:
            # 2. Fallback: Twelve Data
            print(f"yfinance historical failed for {asset.ticker_symbol}: {e_yf}. Trying Twelve Data.")
            db.session.rollback()
            if not td_client:
                print("Twelve Data client not available. Skipping historical update.")
                return
            try:
                ts = td_client.time_series(symbol=asset.ticker_symbol, interval="1day", outputsize=365).as_json()
                for row in ts:
                    price_date = datetime.strptime(row['datetime'], '%Y-%m-%d').date()
                    if not HistoricalPrice.query.filter_by(asset_id=asset.id, price_date=price_date).first():
                        db.session.add(HistoricalPrice(
                            asset_id=asset.id, price_date=price_date,
                            open_price=safe_decimal(row.get('open')), high_price=safe_decimal(row.get('high')),
                            low_price=safe_decimal(row.get('low')), close_price=safe_decimal(row.get('close')),
                            volume=safe_int(row.get('volume'))
                        ))
                db.session.commit()
            except Exception as e_td:
                db.session.rollback()
                print(f"Twelve Data historical also failed for {asset.ticker_symbol}: {e_td}")

    @staticmethod
    def search_assets(query: str):
        """
        Searches for a specific ticker symbol using yfinance and returns its full data.
        Note: This search is intended for ticker symbols (e.g., 'AAPL'), not company names.
        """
        if not query:
            return []

        print(f"Searching yfinance directly for ticker: {query}")
        try:
            ticker = yf.Ticker(query)
            info = ticker.info

            # A valid ticker from yfinance will almost always have a 'longName'.
            # Invalid tickers may return a dict with few keys or no 'longName'.
            if info and info.get('longName'):
                # The function is named search_assets (plural), so it's good practice
                # to return a list containing the single result.
                return [info]
            else:
                print(f"No valid data found for ticker '{query}' on yfinance.")
                return []
        except Exception as e:
            print(f"An error occurred during yfinance search for '{query}': {e}")
            return []

    @staticmethod
    def get_index_data():
        """Fetches the current price and daily change for major market indices using yfinance."""
        index_tickers = {"S&P 500": "^GSPC", "Dow Jones": "^DJI", "Nasdaq": "^IXIC"}
        try:
            data = yf.Tickers(" ".join(index_tickers.values()))
            index_data = []
            for name, ticker in index_tickers.items():
                info = data.tickers[ticker].info
                if info and 'regularMarketPrice' in info and info.get('regularMarketPreviousClose'):
                    change_pct = ((info['regularMarketPrice'] - info['regularMarketPreviousClose']) / info['regularMarketPreviousClose']) * 100
                    index_data.append({"name": name, "ticker": ticker, "price": info.get('regularMarketPrice'), "change_percent": change_pct})
            return index_data
        except Exception as e:
            print(f"Failed to fetch index data: {e}"); return []
    
    @staticmethod
    def update_all_asset_details(asset_id: int = None):
        """Updates full details for assets by merging data from yfinance and Tiingo."""
        assets_to_update = [db.session.get(Asset, asset_id)] if asset_id else Asset.query.filter(Asset.asset_type.in_([AssetType.STOCK, AssetType.ETF])).all()
        if not assets_to_update: print("No assets for detail update."); return

        for asset in assets_to_update:
            if not asset: continue
            print(f"Updating full details for {asset.ticker_symbol}...")
            try:
                # 1. Get primary data from yfinance
                yfinance_data = MarketDataService._get_yfinance_data(asset.ticker_symbol) or {}
                
                # 2. Get supplemental data from Tiingo
                tiingo_data = {}
                if tiingo_client:
                    try:
                        tiingo_data = tiingo_client.get_ticker_metadata(asset.ticker_symbol)
                    except Exception:
                        print(f"Could not fetch Tiingo supplemental data for {asset.ticker_symbol}")

                # 3. Merge data, prioritizing yfinance
                asset.name = yfinance_data.get('name', asset.name)
                if yfinance_data.get('last_price'): asset.last_price = yfinance_data['last_price']
                if yfinance_data.get('previous_close'): asset.previous_close_price = yfinance_data['previous_close']
                
                # Fill in gaps with Tiingo data
                asset.description = yfinance_data.get('description') or tiingo_data.get('description', asset.description)
                asset.exchange_code = yfinance_data.get('exchange_code') or tiingo_data.get('exchangeCode', asset.exchange_code)
                if not asset.list_date and tiingo_data.get('startDate'):
                    asset.list_date = datetime.strptime(tiingo_data['startDate'], '%Y-%m-%d').date()

                asset.price_updated_at = datetime.utcnow()
                db.session.commit()
                print(f"Successfully updated details for {asset.ticker_symbol}.")
            except Exception as e:
                print(f"Could not update details for {asset.ticker_symbol}: {e}")
                db.session.rollback()