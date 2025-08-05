# app/services/market_data_service.py

import os
import yfinance as yf
from nsepython import nse_quote_ltp
from alpha_vantage.fundamentaldata import FundamentalData
from polygon import RESTClient
from datetime import datetime, timedelta
from app.models.models import db, Asset, HistoricalPrice, AssetType
from decimal import Decimal, InvalidOperation
import pandas as pd
import time

# --- Configuration ---
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY')
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY')
fd = FundamentalData(key=ALPHA_VANTAGE_API_KEY, output_format='pandas') if ALPHA_VANTAGE_API_KEY else None
polygon_client = RESTClient(POLYGON_API_KEY) if POLYGON_API_KEY else None

# --- Helper Functions for Robust Data Conversion ---
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
    def _get_live_price_data(ticker: str):
        """[Internal Helper] Fetches live price data using a fallback chain."""
        try:
            price_data = nse_quote_ltp(ticker)
            if price_data and price_data.get('priceInfo') and price_data['priceInfo'].get('lastPrice'):
                print(f"Using nsepython for {ticker}")
                return { "name": price_data['info']['companyName'], "last_price": safe_decimal(price_data['priceInfo']['lastPrice']), "previous_close": safe_decimal(price_data['priceInfo']['previousClose']) }
        except Exception:
            print(f"nsepython failed for {ticker}. Trying yfinance.")
        
        y_ticker = yf.Ticker(ticker)
        info = y_ticker.info
        if info and 'longName' in info:
            return { "name": info.get('longName'), "last_price": safe_decimal(info.get('currentPrice')), "previous_close": safe_decimal(info.get('previousClose')) }
        return None

    @staticmethod
    def find_or_create_asset(ticker: str):
        """Finds an asset by ticker or creates it by fetching comprehensive data."""
        ticker = ticker.upper()
        asset = Asset.query.filter_by(ticker_symbol=ticker).first()
        if asset:
            return asset

        print(f"Asset '{ticker}' not in DB. Fetching from external APIs...")
        try:
            price_info = MarketDataService._get_live_price_data(ticker)
            if not price_info:
                raise ValueError(f"Invalid ticker or no price data found for {ticker}")

            # --- Fetch Rich Details from Polygon.io ---
            polygon_details = None
            if polygon_client:
                try:
                    polygon_details = polygon_client.get_ticker_details(ticker)
                except Exception as e:
                    print(f"Could not fetch Polygon details for {ticker}: {e}")

            # --- Fetch Fundamental Data from Alpha Vantage as a fallback ---
            overview = pd.DataFrame()
            if fd:
                try:
                    overview, _ = fd.get_company_overview(symbol=ticker)
                except Exception as av_error:
                    print(f"Could not fetch Alpha Vantage data for {ticker}: {av_error}.")
            
            # --- Create Asset with the best available data ---
            asset = Asset(
                ticker_symbol=ticker,
                name=getattr(polygon_details, 'name', price_info['name']),
                asset_type=AssetType.STOCK,
                description=getattr(polygon_details, 'description', None),
                homepage_url=getattr(polygon_details, 'homepage_url', None),
                sic_description=getattr(polygon_details, 'sic_description', None),
                list_date=getattr(polygon_details, 'list_date', None),
                market=getattr(polygon_details, 'market', None),
                locale=getattr(polygon_details, 'locale', None),
                primary_exchange=getattr(polygon_details, 'primary_exchange', None),
                total_employees=getattr(polygon_details, 'total_employees', None),
                share_class_shares_outstanding=getattr(polygon_details, 'share_class_shares_outstanding', None),
                last_price=price_info['last_price'],
                previous_close_price=price_info['previous_close'],
                # Use Polygon market cap if available, otherwise fallback to Alpha Vantage
                market_cap=safe_int(getattr(polygon_details, 'market_cap', 0)) or safe_int(overview.loc['MarketCapitalization', 0]) if not overview.empty and 'MarketCapitalization' in overview.index else 0,
                sector=getattr(polygon_details, 'sic_description', None) or (overview.loc['Sector', 0] if not overview.empty and 'Sector' in overview.index else 'N/A'),
                pe_ratio=safe_decimal(overview.loc['PERatio', 0]) if not overview.empty and 'PERatio' in overview.index else Decimal('0.0'),
                eps=safe_decimal(overview.loc['EPS', 0]) if not overview.empty and 'EPS' in overview.index else Decimal('0.0'),
                dividend_yield=safe_decimal(overview.loc['DividendYield', 0]) if not overview.empty and 'DividendYield' in overview.index else Decimal('0.0'),
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
    def update_all_asset_details():
        """
        Fetches and updates the full details (fundamentals, technicals) for all
        existing assets in the database.
        """
        assets_to_update = Asset.query.filter(Asset.asset_type.in_([AssetType.STOCK, AssetType.ETF])).all()
        if not assets_to_update:
            print("No assets found for detail update.")
            return

        for asset in assets_to_update:
            print(f"Updating full details for {asset.ticker_symbol}...")
            try:
                # --- Fetch from Polygon.io for rich details ---
                if polygon_client:
                    details = polygon_client.get_ticker_details(asset.ticker_symbol)
                    asset.name = getattr(details, 'name', asset.name)
                    asset.description = getattr(details, 'description', asset.description)
                    asset.homepage_url = getattr(details, 'homepage_url', asset.homepage_url)
                    asset.sic_description = getattr(details, 'sic_description', asset.sic_description)
                    asset.market_cap = safe_int(getattr(details, 'market_cap', asset.market_cap))
                
                # --- Fetch from Alpha Vantage for fundamentals ---
                if fd:
                    overview, _ = fd.get_company_overview(symbol=asset.ticker_symbol)
                    if not overview.empty:
                        asset.pe_ratio = safe_decimal(overview.loc['PERatio', 0])
                        asset.eps = safe_decimal(overview.loc['EPS', 0])
                        asset.dividend_yield = safe_decimal(overview.loc['DividendYield', 0])
                    time.sleep(12) # Respect rate limit

                db.session.commit()
                print(f"Successfully updated details for {asset.ticker_symbol}.")

            except Exception as e:
                print(f"Could not update details for {asset.ticker_symbol}: {e}")
                db.session.rollback()
                time.sleep(12) # Wait even if there's an error to avoid spamming a failing API

    @staticmethod
    def update_asset_prices():
        """Fetches the latest market price for all assets using the best source."""
        print("Starting bulk asset price update...")
        assets_to_update = Asset.query.filter(Asset.asset_type.in_([AssetType.STOCK, AssetType.ETF])).all()
        if not assets_to_update:
            print("No assets to update.")
            return

        for asset in assets_to_update:
            price_data = MarketDataService._get_live_price_data(asset.ticker_symbol)
            if price_data and price_data.get('last_price'):
                asset.last_price = price_data['last_price']
                asset.previous_close_price = price_data['previous_close']
                asset.price_updated_at = datetime.utcnow()
                print(f"Updated {asset.ticker_symbol}: Price={asset.last_price}")
            else:
                print(f"Could not find price data for {asset.ticker_symbol}. Skipping.")
        
        db.session.commit()
        print("Database price update finished.")
    
    @staticmethod
    def get_asset_details(ticker: str):
        """Gets detailed fundamental, technical, and historical data for an asset."""
        asset = MarketDataService.find_or_create_asset(ticker)
        
        latest_history = HistoricalPrice.query.filter_by(asset_id=asset.id).order_by(HistoricalPrice.price_date.desc()).first()
        if not latest_history or latest_history.price_date < (datetime.utcnow().date() - timedelta(days=1)):
            MarketDataService.update_historical_data(asset.id)

        historical_data = HistoricalPrice.query.filter_by(asset_id=asset.id).order_by(HistoricalPrice.price_date.asc()).all()
        
        return {
            "asset_id": asset.id,
            "ticker_symbol": asset.ticker_symbol,
            "name": asset.name,
            "description": asset.description,
            "homepage_url": asset.homepage_url,
            "list_date": asset.list_date.isoformat() if asset.list_date else None,
            "market": asset.market,
            "locale": asset.locale,
            "last_price": float(asset.last_price) if asset.last_price is not None else 0.0,
            "previous_close_price": float(asset.previous_close_price) if asset.previous_close_price is not None else 0.0,
            "fundamentals": {
                "market_cap": asset.market_cap,
                "sector": asset.sector or asset.sic_description,
                "pe_ratio": float(asset.pe_ratio) if asset.pe_ratio is not None else 0.0,
                "eps": float(asset.eps) if asset.eps is not None else 0.0,
                "dividend_yield": float(asset.dividend_yield) if asset.dividend_yield is not None else 0.0,
            },
            "historical_data": [{"date": h.price_date.isoformat(), "close": float(h.close_price)} for h in historical_data]
        }

    @staticmethod
    def update_asset_prices():
        """Fetches the latest market price for all assets using the best source."""
        print("Starting bulk asset price update...")
        assets_to_update = Asset.query.filter(Asset.asset_type.in_([AssetType.STOCK, AssetType.ETF])).all()
        if not assets_to_update:
            print("No assets to update.")
            return

        for asset in assets_to_update:
            price_data = MarketDataService._get_live_price_data(asset.ticker_symbol)
            if price_data and price_data.get('last_price'):
                asset.last_price = price_data['last_price']
                asset.previous_close_price = price_data['previous_close']
                asset.price_updated_at = datetime.utcnow()
                print(f"Updated {asset.ticker_symbol}: Price={asset.last_price}")
            else:
                print(f"Could not find price data for {asset.ticker_symbol}. Skipping.")
        
        db.session.commit()
        print("Database price update finished.")


    @staticmethod
    def update_historical_data(asset_id: int, period="1y"):
        """Fetches and stores historical data for a given asset using yfinance."""
        asset = Asset.query.get(asset_id)
        if not asset or asset.asset_type not in [AssetType.STOCK, AssetType.ETF, AssetType.INDEX]:
            return

        print(f"Updating historical data for {asset.ticker_symbol}...")
        try:
            ticker_obj = yf.Ticker(asset.ticker_symbol)
            hist = ticker_obj.history(period=period)
            
            for index, row in hist.iterrows():
                record_exists = HistoricalPrice.query.filter_by(asset_id=asset.id, price_date=index.date()).first()
                if not record_exists:
                    new_price = HistoricalPrice(
                        asset_id=asset.id,
                        price_date=index.date(),
                        open_price=safe_decimal(row.get('Open')),
                        high_price=safe_decimal(row.get('High')),
                        low_price=safe_decimal(row.get('Low')),
                        close_price=safe_decimal(row.get('Close')),
                        volume=safe_int(row.get('Volume'))
                    )
                    db.session.add(new_price)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to update historical data for {asset.ticker_symbol}: {e}")
    
    @staticmethod
    def get_index_data():
        """
        Fetches the current price and daily change for major market indices.
        """
        index_tickers = {
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI",
            "Nasdaq": "^IXIC",
            "Russell 2000": "^RUT",
            "DAX": "^GDAXI",
            "CAC 40": "^FCHI",
            "FTSE 100": "^FTSE",
        }
        try:
            tickers_str = " ".join(index_tickers.values())
            data = yf.Tickers(tickers_str)
            
            index_data = []
            for name, ticker in index_tickers.items():
                info = data.tickers[ticker].info
                if info and 'regularMarketPrice' in info:
                    index_data.append({
                        "name": name,
                        "ticker": ticker,
                        "price": info.get('regularMarketPrice'),
                        "change_percent": info.get('regularMarketChangePercent', 0) * 100
                    })
            return index_data
        except Exception as e:
            print(f"Failed to fetch index data: {e}")
            return []