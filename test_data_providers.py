# test_data_providers.py

import os
import yfinance as yf
from dotenv import load_dotenv
from twelvedata import TDClient
from tiingo import TiingoClient
import pprint

def run_test():
    """
    A simple, standalone script to test the connection and raw data output
    from the Twelve Data, Tiingo, and yfinance APIs for a specific ticker (AAPL).
    """
    print("--- Starting Data Provider API Test ---")

    # --- 1. Load Environment Variables ---
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(dotenv_path):
        print("\nNOTE: .env file not found. Skipping tests for Twelve Data and Tiingo.")
        # Initialize keys as None so the blocks are skipped gracefully
        twelve_data_key = None
        tiingo_key = None
    else:
        load_dotenv(dotenv_path=dotenv_path)
        twelve_data_key = os.environ.get('TWELVE_DATA_API_KEY')
        tiingo_key = os.environ.get('TIINGO_API_KEY')


    # --- 2. Test Twelve Data API ---
    print("\n--- Testing Twelve Data ---")
    if not twelve_data_key or twelve_data_key == 'YOUR_TWELVE_DATA_KEY':
        print("RESULT: TWELVE_DATA_API_KEY is not set in your .env file. Skipping test.")
    else:
        try:
            td_client = TDClient(apikey=twelve_data_key)
            print("Twelve Data client initialized successfully.")
            
            ticker = 'AAPL'
            print(f"Fetching Quote for {ticker}...")
            quote = td_client.quote(symbol=ticker).as_json()
            
            print("\n--- SUCCESS! Raw Quote Data from Twelve Data ---")
            pprint.pprint(quote)
            print("---------------------------------------------")

        except Exception as e:
            print(f"\nERROR: An exception occurred with Twelve Data: {e}")

    # --- 3. Test Tiingo API ---
    print("\n--- Testing Tiingo ---")
    if not tiingo_key or tiingo_key == 'YOUR_TIINGO_KEY':
        print("RESULT: TIINGO_API_KEY is not set in your .env file. Skipping test.")
    else:
        try:
            # Note: Tiingo client configuration is a dictionary
            config = {'api_key': tiingo_key}
            tiingo_client = TiingoClient(config)
            print("Tiingo client initialized successfully.")

            ticker = 'AAPL'
            print(f"Fetching Metadata for {ticker}...")
            metadata = tiingo_client.get_ticker_metadata(ticker)

            print("\n--- SUCCESS! Raw Metadata from Tiingo ---")
            pprint.pprint(metadata)
            print("----------------------------------------")

        except Exception as e:
            print(f"\nERROR: An exception occurred with Tiingo: {e}")
            
    # --- 4. Test yfinance ---
    print("\n--- Testing yfinance ---")
    # yfinance does not require an API key
    try:
        ticker_symbol = 'AAPL'
        print(f"Initializing ticker for {ticker_symbol}...")
        ticker = yf.Ticker(ticker_symbol)
        
        # The .info attribute contains a dictionary of various data points
        info = ticker.info
        
        print(f"\n--- SUCCESS! Raw Info Data from yfinance for {ticker_symbol} ---")
        pprint.pprint(info)
        print("-----------------------------------------------------")

    except Exception as e:
        print(f"\nERROR: An exception occurred with yfinance: {e}")


if __name__ == '__main__':
    run_test()