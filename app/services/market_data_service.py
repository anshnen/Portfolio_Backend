import yfinance as yf
from datetime import datetime, timedelta
from app.models.models import db, Asset, HistoricalPrice
from decimal import Decimal

class MarketDataService:
    @staticmethod
    def find_or_create_asset(ticker: str):
        """Finds an asset by ticker or creates it by fetching data from yfinance."""
        ticker = ticker.upper()
        asset = Asset.query.filter_by(ticker_symbol=ticker).first()
        if asset:
            return asset

        print(f"Asset '{ticker}' not in DB. Fetching from external API...")
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info
            if not info or 'longName' not in info:
                raise ValueError(f"Invalid ticker or no data found for {ticker}")

            asset = Asset(
                ticker_symbol=info.get('symbol', ticker).upper(),
                name=info.get('longName'),
                asset_type=info.get('quoteType', 'STOCK').upper(),
                market_cap=info.get('marketCap'),
                sector=info.get('sector'),
                last_price=Decimal(str(info.get('currentPrice', 0))),
                previous_close_price=Decimal(str(info.get('previousClose', 0))),
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
    def get_asset_details(ticker: str):
        """Gets detailed information and historical data for an asset."""
        asset = MarketDataService.find_or_create_asset(ticker)
        
        # Fetch historical data if it's stale or missing
        latest_history = HistoricalPrice.query.filter_by(asset_id=asset.id).order_by(HistoricalPrice.price_date.desc()).first()
        if not latest_history or latest_history.price_date < (datetime.utcnow().date() - timedelta(days=1)):
            MarketDataService.update_historical_data(asset.id)

        historical_data = HistoricalPrice.query.filter_by(asset_id=asset.id).order_by(HistoricalPrice.price_date.asc()).all()
        
        return {
            "asset_id": asset.id,
            "ticker_symbol": asset.ticker_symbol,
            "name": asset.name,
            "last_price": float(asset.last_price) if asset.last_price else None,
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
        """Fetches and stores historical data for a given asset."""
        asset = Asset.query.get(asset_id)
        if not asset or asset.asset_type not in ['STOCK', 'ETF', 'INDEX']:
            return

        print(f"Updating historical data for {asset.ticker_symbol}...")
        try:
            ticker_obj = yf.Ticker(asset.ticker_symbol)
            hist = ticker_obj.history(period=period)
            
            for index, row in hist.iterrows():
                # Check if a record for this date already exists
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
        """Searches for assets by ticker or name."""
        search = f"%{query}%"
        assets = Asset.query.filter(
            (Asset.ticker_symbol.ilike(search)) | (Asset.name.ilike(search))
        ).limit(10).all()
        return [{"ticker": a.ticker_symbol, "name": a.name} for a in assets]