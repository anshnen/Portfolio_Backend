# tests/test_api/test_market_data_routes.py

from tests.data.mock_api_data import MOCK_AAPL_DATA

def test_get_asset_details_success(client, mocker):
    """
    GIVEN a valid ticker symbol
    WHEN the GET /api/v1/market/asset/<ticker> endpoint is called
    AND the external API call within the service is mocked to return valid data
    THEN it should return a 200 OK status with the correct asset details
    """
    # ARRANGE
    # Use mocker to replace the external API call with our mock data.
    # This isolates the test to only the API layer's functionality.
    mocker.patch(
        'app.services.market_data_service.MarketDataService.get_price_from_source',
        return_value=MOCK_AAPL_DATA
    )
    
    # ACT: Make the HTTP request using the test client
    response = client.get('/api/v1/market/asset/AAPL')
    json_data = response.get_json()

    # ASSERT: Check the HTTP response and the JSON payload
    assert response.status_code == 200
    assert json_data['ticker_symbol'] == 'AAPL'
    assert json_data['name'] == 'Apple Inc.'
    assert json_data['fundamentals']['sector'] == 'Technology'

def test_search_assets_query_too_short(client):
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
    assert 'error' in json_data
    assert "at least 2 characters long" in json_data['error']
