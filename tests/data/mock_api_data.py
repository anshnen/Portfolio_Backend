from decimal import Decimal

# Mock data simulating a response from yfinance or nsepython
MOCK_AAPL_DATA = {
    "name": "Apple Inc.",
    "last_price": Decimal("175.50"),
    "previous_close": Decimal("172.00"),
    "sector": "Technology",
    "market_cap": 3000000000000
}

MOCK_RELIANCE_DATA = {
    "name": "Reliance Industries Limited",
    "last_price": Decimal("2500.00"),
    "previous_close": Decimal("2450.00"),
    "sector": "Energy",
    "market_cap": 17000000000000
}
MOCK_TCS_DATA = {
    "name": "Tata Consultancy Services",
    "last_price": Decimal("3500.00"),
    "previous_close": Decimal("3450.00"),
    "sector": "IT Services",
    "market_cap": 1300000000000
}