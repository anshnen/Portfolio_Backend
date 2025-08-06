# test_data_providers.py

import os
from dotenv import load_dotenv
from twelvedata import TDClient
from tiingo import TiingoClient
import pprint

def run_test():
    """
    A simple, standalone script to test the connection and raw data output
    from the Twelve Data and Tiingo APIs for a specific ticker (AAPL).
    """
    print("--- Starting Data Provider API Test ---")

    # --- 1. Load Environment Variables ---
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(dotenv_path):
        print("\nERROR: .env file not found. Please ensure it exists in the project root.")
        return

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
            tiingo_client = TiingoClient({'api_key': tiingo_key})
            print("Tiingo client initialized successfully.")

            ticker = 'AAPL'
            print(f"Fetching Metadata for {ticker}...")
            metadata = tiingo_client.get_ticker_metadata(ticker)

            print("\n--- SUCCESS! Raw Metadata from Tiingo ---")
            pprint.pprint(metadata)
            print("----------------------------------------")

        except Exception as e:
            print(f"\nERROR: An exception occurred with Tiingo: {e}")


if __name__ == '__main__':
    run_test()
