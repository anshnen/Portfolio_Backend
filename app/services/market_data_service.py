import yfinance as yf
from datetime import datetime
from ..models.models import db, Asset

class MarketDataService:
    
    @staticmethod
    def update_asset_prices():
        
        print("Fetching all unique asset tickers from the database...")
        assets_to_update = Asset.query.filter(Asset.asset_type != 'CASH').all()
        
        if not assets_to_update:
            print("No non-cash assets to update.")
            return

        tickers = [asset.ticker_symbol for asset in assets_to_update]
        tickers_str = " ".join(tickers)
        print(f"Fetching market data for: {tickers_str}")

        try:
            ticker_data = yf.Tickers(tickers_str)

            for asset in assets_to_update:
                try:
                    info = ticker_data.tickers[asset.ticker_symbol].info
                    
                    # Get current price, with a fallback to previous close
                    last_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')

                    if last_price and prev_close:
                        asset.last_price = last_price
                        asset.previous_close_price = prev_close
                        asset.price_updated_at = datetime.utcnow()
                        print(f"Updated {asset.ticker_symbol}: Last Price={last_price}, Prev Close={prev_close}")
                    else:
                        print(f"Could not find price data for {asset.ticker_symbol}. Skipping.")

                except Exception as e:
                    print(f"Error processing ticker {asset.ticker_symbol}: {e}")

            db.session.commit()
            print("Database successfully updated with new market prices.")

        except Exception as e:
            print(f"An error occurred while fetching data from yfinance: {e}")
            db.session.rollback()