import os
import yfinance as yf
from nsepython import nse_quote_ltp
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.techindicators import TechIndicators
from datetime import datetime, timedelta
from app.models.models import db, Asset, HistoricalPrice
from decimal import Decimal
import pandas as pd

# --- Configuration ---
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', 'YOUR_DEFAULT_KEY')
fd = FundamentalData(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
ti = TechIndicators(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

class MarketDataService:
    @staticmethod
    def find_or_create_asset(ticker: str):
        """Finds an asset by ticker or creates it by fetching comprehensive data."""
        ticker = ticker.upper()
        asset = Asset.query.filter_by(ticker_symbol=ticker).first()
        if asset:
            return asset

        print(f"Asset '{ticker}' not in DB. Fetching from external APIs...")
        try:
            # --- Data Fetching Chain ---
            # 1. Try nsepython for price
            try:
                price_data = nse_quote_ltp(ticker)
                name = price_data['info']['companyName']
                last_price = Decimal(str(price_data['priceInfo']['lastPrice']))
                prev_close = Decimal(str(price_data['priceInfo']['previousClose']))
            except Exception:
                # 2. Fallback to yfinance for price and basic info
                y_ticker = yf.Ticker(ticker)
                info = y_ticker.info
                if not info or 'longName' not in info:
                    raise ValueError(f"Invalid ticker or no data found for {ticker}")
                name = info.get('longName')
                last_price = Decimal(str(info.get('currentPrice', 0)))
                prev_close = Decimal(str(info.get('previousClose', 0)))

            # 3. Fetch fundamental and technical data from Alpha Vantage
            try:
                overview, _ = fd.get_company_overview(symbol=ticker)
                sma50, _ = ti.get_sma(symbol=ticker, interval='daily', time_period=50, series_type='close')
                sma200, _ = ti.get_sma(symbol=ticker, interval='daily', time_period=200, series_type='close')
            except Exception as av_error:
                print(f"Could not fetch Alpha Vantage data for {ticker}: {av_error}. Proceeding with basic data.")
                overview = pd.DataFrame()
                sma50 = pd.DataFrame()
                sma200 = pd.DataFrame()

            asset = Asset(
                ticker_symbol=ticker,
                name=name,
                asset_type='STOCK',
                last_price=last_price,
                previous_close_price=prev_close,
                market_cap=int(overview['MarketCapitalization'].iloc[0]) if not overview.empty and 'MarketCapitalization' in overview and overview['MarketCapitalization'].iloc[0] != 'None' else None,
                sector=overview['Sector'].iloc[0] if not overview.empty and 'Sector' in overview else 'N/A',
                pe_ratio=Decimal(str(overview['PERatio'].iloc[0])) if not overview.empty and 'PERatio' in overview and overview['PERatio'].iloc[0] != 'None' else None,
                eps=Decimal(str(overview['EPS'].iloc[0])) if not overview.empty and 'EPS' in overview and overview['EPS'].iloc[0] != 'None' else None,
                dividend_yield=Decimal(str(overview['DividendYield'].iloc[0])) if not overview.empty and 'DividendYield' in overview and overview['DividendYield'].iloc[0] != 'None' else None,
                beta=Decimal(str(overview['Beta'].iloc[0])) if not overview.empty and 'Beta' in overview and overview['Beta'].iloc[0] != 'None' else None,
                fifty_day_average=Decimal(str(sma50['SMA'].iloc[0])) if not sma50.empty else None,
                two_hundred_day_average=Decimal(str(sma200['SMA'].iloc[0])) if not sma200.empty else None,
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
        """Gets detailed fundamental, technical, and historical data for an asset."""
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
            "previous_close_price": float(asset.previous_close_price) if asset.previous_close_price else None,
            "fundamentals": {
                "market_cap": asset.market_cap,
                "sector": asset.sector,
                "pe_ratio": float(asset.pe_ratio) if asset.pe_ratio else None,
                "eps": float(asset.eps) if asset.eps else None,
                "dividend_yield": float(asset.dividend_yield) if asset.dividend_yield else None,
                "beta": float(asset.beta) if asset.beta else None,
            },
            "technicals": {
                "fifty_day_average": float(asset.fifty_day_average) if asset.fifty_day_average else None,
                "two_hundred_day_average": float(asset.two_hundred_day_average) if asset.two_hundred_day_average else None,
            },
            "historical_data": [{"date": h.price_date.isoformat(), "close": float(h.close_price)} for h in historical_data]
        }

    @staticmethod
    def update_asset_prices():
        """Fetches the latest market price for all assets using the best source."""
        print("Fetching all unique asset tickers for price update...")
        assets_to_update = Asset.query.filter(Asset.asset_type.in_(['STOCK', 'ETF'])).all()
        if not assets_to_update:
            print("No assets to update.")
            return

        for asset in assets_to_update:
            try:
                # Use the same data fetching chain as find_or_create_asset
                price_data = nse_quote_ltp(asset.ticker_symbol)
                asset.last_price = Decimal(str(price_data['priceInfo']['lastPrice']))
                asset.previous_close_price = Decimal(str(price_data['priceInfo']['previousClose']))
                asset.price_updated_at = datetime.utcnow()
                print(f"Updated {asset.ticker_symbol} using nsepython.")
            except Exception:
                try:
                    y_ticker = yf.Ticker(asset.ticker_symbol)
                    info = y_ticker.info
                    asset.last_price = Decimal(str(info.get('currentPrice', 0)))
                    asset.previous_close_price = Decimal(str(info.get('previousClose', 0)))
                    asset.price_updated_at = datetime.utcnow()
                    print(f"Updated {asset.ticker_symbol} using yfinance.")
                except Exception as yf_error:
                    print(f"Could not update price for {asset.ticker_symbol} from any source: {yf_error}")
        
        db.session.commit()
        print("Database price update finished.")

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
