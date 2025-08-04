import os
from dotenv import load_dotenv
from alpha_vantage.fundamentaldata import FundamentalData
import pandas as pd

def run_test():
    """
    A simple, standalone script to test the connection to the Alpha Vantage API
    and fetch data for a specific ticker (AAPL).
    """
    print("--- Starting Alpha Vantage API Test ---")

    # --- 1. Load Environment Variables ---
    # Construct the path to the .env file in the project root
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(dotenv_path):
        print("\nERROR: .env file not found in the project root.")
        print("Please ensure the file exists and contains your ALPHA_VANTAGE_API_KEY.")
        return

    load_dotenv(dotenv_path=dotenv_path)
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')

    # --- 2. Check for API Key ---
    if not api_key or api_key == 'YOUR_DEFAULT_KEY' or api_key == "YOUR_API_KEY":
        print("\nERROR: ALPHA_VANTAGE_API_KEY is not set correctly in your .env file.")
        print("Please get a free key from https://www.alphavantage.co/support/#api-key and add it to your .env file.")
        return
    
    print(f"API Key found: ...{api_key[-4:]}") # Print last 4 chars for verification

    # --- 3. Initialize API Client ---
    try:
        # Set pandas to display all columns for better readability
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        fd = FundamentalData(key=api_key, output_format='pandas')
        print("Alpha Vantage client initialized successfully.")
    except Exception as e:
        print(f"\nERROR: Failed to initialize Alpha Vantage client: {e}")
        return

    # --- 4. Fetch and Display Data ---
    ticker = 'AAPL'
    print(f"\nFetching Company Overview data for {ticker}...")
    try:
        overview, _ = fd.get_company_overview(symbol=ticker)
        
        if overview.empty:
            print("\nRESULT: The API returned an empty DataFrame.")
            print("This usually means one of two things:")
            print("1. Your API key is invalid or has reached its rate limit.")
            print("2. The ticker symbol might not be available via Alpha Vantage.")
        else:
            # Check for the common rate limit message
            if 'Note' in overview.columns and 'API call frequency' in overview['Note'].iloc[0]:
                 print("\nRESULT: Received a rate limit warning from the API.")
                 print(overview['Note'].iloc[0])
            else:
                print("\n--- SUCCESS! Raw Data Received ---")
                print(overview.T) # Transpose for better readability
                print("---------------------------------")

    except Exception as e:
        print(f"\nERROR: An exception occurred while fetching data: {e}")
        print("This could be due to an invalid API key, rate limiting, or a network issue.")

if __name__ == '__main__':
    run_test()
