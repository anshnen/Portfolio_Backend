# app/services/market_data_service.py

import yfinance as yf
from nsetools import Nse
from datetime import datetime, timedelta
from app.models.models import db, Asset, HistoricalPrice
from decimal import Decimal

# Initialize the NSE tool
nse = Nse()

class MarketDataService:
    @staticmethod
    def get_price_from_source(ticker: str):
        """
        Fetches the last price and previous close from the best available source.
        Prioritizes nsetools for valid NSE tickers, otherwise uses yfinance.
        """
        try:
            # Prioritize NSE for Indian stocks
            if nse.is_valid_code(ticker):
                print(f"Using nsetools for NSE ticker: {ticker}")
                quote = nse.get_quote(ticker)
                if quote and quote.get('lastPrice'):
                    return {
                        "last_price": Decimal(str(quote.get('lastPrice', 0))),
                        "previous_close": Decimal(str(quote.get('previousClose', 0))),
                        "name": quote.get('companyName', 'N/A'),
                        "sector": quote.get('industry', 'N/A'),
                        "market_cap": quote.get('marketCap')
                    }
        except Exception as e:
            print(f"nsetools failed for {ticker}: {e}. Falling back to yfinance.")

        # Fallback to yfinance for non-NSE stocks or if nsetools fails
        print(f"Using yfinance for ticker: {ticker}")
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        if not info or 'longName' not in info:
            return None
        
        return {
            "last_price": Decimal(str(info.get('currentPrice') or info.get('regularMarketPrice', 0))),
            "previous_close": Decimal(str(info.get('previousClose') or info.get('regularMarketPreviousClose', 0))),
            "name": info.get('longName'),
            "sector": info.get('sector'),
            "market_cap": info.get('marketCap')
        }

    @staticmethod
    def update_asset_prices():
        """
        Fetches the latest market price for all assets using the best source.
        """
        print("Fetching all unique asset tickers for price update...")
        assets_to_update = Asset.query.filter(Asset.asset_type.in_(['STOCK', 'ETF'])).all()
        if not assets_to_update:
            print("No assets to update.")
            return

        for asset in assets_to_update:
            price_data = MarketDataService.get_price_from_source(asset.ticker_symbol)
            if price_data and price_data['last_price'] > 0:
                asset.last_price = price_data['last_price']
                asset.previous_close_price = price_data['previous_close']
                asset.price_updated_at = datetime.utcnow()
                print(f"Updated {asset.ticker_symbol}: Last Price={asset.last_price}, Prev Close={asset.previous_close_price}")
            else:
                print(f"Could not find price data for {asset.ticker_symbol}. Skipping.")
        
        db.session.commit()
        print("Database successfully updated with new market prices.")

    @staticmethod
    def find_or_create_asset(ticker: str):
        """Finds an asset or creates it by fetching data from the best source."""
        ticker = ticker.upper()
        asset = Asset.query.filter_by(ticker_symbol=ticker).first()
        if asset:
            return asset

        print(f"Asset '{ticker}' not in DB. Fetching from external API...")
        asset_info = MarketDataService.get_price_from_source(ticker)
        
        if not asset_info:
            raise ValueError(f"Could not find a valid asset for ticker '{ticker}'.")
        
        asset = Asset(
            ticker_symbol=ticker,
            name=asset_info['name'],
            asset_type='STOCK', # Defaulting to stock, can be enhanced
            market_cap=asset_info.get('market_cap'),
            sector=asset_info.get('sector'),
            last_price=asset_info['last_price'],
            previous_close_price=asset_info['previous_close'],
            price_updated_at=datetime.utcnow()
        )
        db.session.add(asset)
        db.session.commit()
        print(f"New asset '{asset.name}' created.")
        return asset

    @staticmethod
    def get_asset_details(ticker: str):
        """Gets detailed information and historical data for an asset."""
        asset = MarketDataService.find_or_create_asset(ticker)
        
        latest_history = HistoricalPrice.query.filter_by(asset_id=asset.id).order_by(HistoricalPrice.price_date.desc()).first()
        if not latest_history or latest_history.price_date < (datetime.utcnow().date() - timedelta(days=1)):
            MarketDataService.update_historical_data(asset.id)

        historical_data = HistoricalPrice.query.filter_by(asset_id=asset.id).order_by(HistoricalPrice.price_date.asc()).all()
        
        return {
            "asset_id": asset.id,
            "ticker_symbol": asset.ticker_symbol,
            "name": asset.name,
            "last_price": float(asset.last_price) if asset.last_price else None,
            "previous_close_price": float(asset.previous_close_price) if asset.previous_close_price else None,
            "market_cap": asset.market_cap,
            "sector": asset.sector,
            "historical_data": [
                {
                    "date": h.price_date.isoformat(),
                    "open": float(h.open_price) if h.open_price else None,
                    "high": float(h.high_price) if h.high_price else None,
                    "low": float(h.low_price) if h.low_price else None,
                    "close": float(h.close_price),
                    "volume": h.volume
                } for h in historical_data
            ]
        }

    @staticmethod
    def update_historical_data(asset_id: int, period="1y"):
        """Fetches and stores historical data for a given asset using yfinance."""
        asset = Asset.query.get(asset_id)
        if not asset or asset.asset_type not in ['STOCK', 'ETF', 'INDEX']:
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
                        open_price=Decimal(str(row['Open'])),
                        high_price=Decimal(str(row['High'])),
                        low_price=Decimal(str(row['Low'])),
                        close_price=Decimal(str(row['Close'])),
                        volume=row['Volume']
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