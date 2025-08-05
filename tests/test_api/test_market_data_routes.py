# tests/test_api/test_market_data_routes.py

from tests.data.mock_api_data import MOCK_AAPL_DATA

def test_get_asset_details_success_api(client, mocker):
    """
    GIVEN a valid ticker symbol
    WHEN the GET /api/v1/market/asset/<ticker> endpoint is called
    AND the external API call within the service is mocked
    THEN it should return a 200 OK with the correct asset details
    """
    # ARRANGE
    mocker.patch(
        'app.services.market_data_service.MarketDataService.find_or_create_asset',
        return_value=mocker.Mock(
            id=1, ticker_symbol='AAPL', name='Apple Inc.', last_price=MOCK_AAPL_DATA['last_price'],
            sector=MOCK_AAPL_DATA['sector'], market_cap=MOCK_AAPL_DATA['market_cap']
        )
    )
    mocker.patch('app.services.market_data_service.MarketDataService.update_historical_data')
    mocker.patch('app.models.models.HistoricalPrice.query.filter_by.return_value.order_by.return_value.desc.return_value.first.return_value', None)
    mocker.patch('app.models.models.HistoricalPrice.query.filter_by.return_value.order_by.return_value.asc.return_value.all.return_value', [])

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