# tests/test_api/test_account_and_market_routes.py

from decimal import Decimal
from app.models.models import User, Portfolio, Account, Asset, AssetType
from tests.data.mock_api_data import MOCK_AAPL_DATA

def test_get_accounts_for_portfolio_api(client, db):
    """
    GIVEN a portfolio with a single account
    WHEN the GET /api/v1/accounts/portfolio/<id> endpoint is called
    THEN it should return a 200 OK with a list containing that one account
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    # FIX: Create only a single account without the removed 'account_type'
    account = Account(name="Primary Account", balance=Decimal("5000.00"), portfolio=portfolio)
    db.session.add_all([user, portfolio, account])
    db.session.commit()

    # ACT
    response = client.get(f'/api/v1/accounts/portfolio/{portfolio.id}')
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    assert isinstance(json_data, list)
    assert len(json_data) == 1
    assert json_data[0]['name'] == 'Primary Account'

def test_manage_funds_deposit_api(client, db):
    """
    GIVEN an account with an initial balance
    WHEN a POST request is made to the /api/v1/accounts/<id>/funds endpoint to DEPOSIT
    THEN it should return a 200 OK and the account balance should be updated
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    # FIX: Create only a single account without the removed 'account_type'
    account = Account(name="Primary Account", balance=Decimal("1000.00"), portfolio=portfolio)
    db.session.add_all([user, portfolio, account])
    db.session.commit()

    payload = { "action": "DEPOSIT", "amount": 500.00 }

    # ACT
    response = client.post(f'/api/v1/accounts/{account.id}/funds', json=payload)
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    assert json_data['message'] == "Deposit successful."
    assert json_data['new_balance'] == 1500.00
    
    updated_account = db.session.get(Account, account.id)
    assert updated_account.balance == Decimal("1500.00")

# --- Market Data Routes ---

def test_get_asset_details_success_api(client, mocker):
    """
    GIVEN a valid ticker symbol
    WHEN the GET /api/v1/market/asset/<ticker> endpoint is called
    AND the external API call within the service is mocked
    THEN it should return a 200 OK with the correct asset details
    """
    # ARRANGE
    mock_asset = Asset(
        id=1, ticker_symbol='AAPL', name='Apple Inc.', asset_type=AssetType.STOCK,
        last_price=MOCK_AAPL_DATA['last_price'],
        market_cap=MOCK_AAPL_DATA['market_cap'], eps=None,
        dividend_yield=None, beta=None, fifty_day_average=None, two_hundred_day_average=None
    )
    mocker.patch(
        'app.services.market_data_service.MarketDataService.find_or_create_asset',
        return_value=mock_asset
    )
    mocker.patch(
        'app.services.market_data_service.MarketDataService.update_historical_data',
        return_value=None
    )
    
    mock_query = mocker.patch('app.models.models.HistoricalPrice.query')
    mock_query.filter_by.return_value.order_by.return_value.desc.return_value.first.return_value = None
    mock_query.filter_by.return_value.order_by.return_value.asc.return_value.all.return_value = []

    # ACT
    response = client.get('/api/v1/market/asset/AAPL')
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    assert json_data['ticker_symbol'] == 'AAPL'
    assert json_data['name'] == 'Apple Inc.'
    assert json_data['fundamentals']['sector'] == 'Technology'

def test_search_assets_query_too_short_api(client):
    """
    GIVEN a search query that is too short
    WHEN the GET /api/v1/market/search endpoint is called
    THEN it should return a 400 Bad Request error
    """
    # ACT
    response = client.get('/api/v1/market/search?q=A')
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 400
    assert "at least 2 characters long" in json_data['error']

def test_search_assets_success_api(client, db):
    """
    GIVEN assets existing in the database
    WHEN the GET /api/v1/market/search endpoint is called with a valid query
    THEN it should return a 200 OK with a list of matching assets
    """
    # ARRANGE
    asset1 = Asset(ticker_symbol='AAPL', name='Apple Inc.', asset_type=AssetType.STOCK)
    asset2 = Asset(ticker_symbol='AMZN', name='Amazon.com, Inc.', asset_type=AssetType.STOCK)
    db.session.add_all([asset1, asset2])
    db.session.commit()

    # ACT
    response = client.get('/api/v1/market/search?q=App')
    json_data = response.get_json()

    # ASSERT
    assert response.status_code == 200
    assert isinstance(json_data, list)
    assert len(json_data) == 1
    assert json_data[0]['ticker'] == 'AAPL'
