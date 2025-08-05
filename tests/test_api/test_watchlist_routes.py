# tests/test_api/test_watchlist_routes.py

from app.models.models import User, Portfolio, Watchlist, Asset, WatchlistItem
from tests.data.mock_api_data import MOCK_AAPL_DATA

def test_create_and_get_watchlist_api(client, db):
    """
    GIVEN a portfolio
    WHEN a POST request is made to /api/v1/watchlists to create a new one
    AND a GET request is made to retrieve it
    THEN the responses should be successful and contain the correct data
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    db.session.add_all([user, portfolio])
    db.session.commit()

    # ACT (Create)
    create_payload = {"portfolio_id": portfolio.id, "name": "My Tech Stocks"}
    create_response = client.post('/api/v1/watchlists', json=create_payload)
    create_json = create_response.get_json()

    # ASSERT (Create)
    assert create_response.status_code == 201
    assert create_json['name'] == "My Tech Stocks"

    # ACT (Get)
    get_response = client.get(f'/api/v1/watchlists/{portfolio.id}')
    get_json = get_response.get_json()

    # ASSERT (Get)
    assert get_response.status_code == 200
    assert len(get_json) == 1
    assert get_json[0]['name'] == "My Tech Stocks"
    assert get_json[0]['items'] == []

def test_add_and_remove_item_from_watchlist_api(client, db, mocker):
    """
    GIVEN a watchlist
    WHEN an item is added via POST and then removed via DELETE
    THEN the API should respond correctly and the database state should be updated
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    watchlist = Watchlist(name="Test Watchlist", portfolio=portfolio)
    db.session.add_all([user, portfolio, watchlist])
    db.session.commit()

    mocker.patch(
        'app.services.market_data_service.MarketDataService.find_or_create_asset',
        return_value=Asset(id=99, ticker_symbol="AAPL", name="Apple Inc")
    )

    # ACT (Add)
    add_payload = {"ticker": "AAPL"}
    add_response = client.post(f'/api/v1/watchlists/{watchlist.id}/items', json=add_payload)
    
    # ASSERT (Add)
    assert add_response.status_code == 201
    assert WatchlistItem.query.count() == 1

    # ACT (Remove)
    remove_response = client.delete(f'/api/v1/watchlists/{watchlist.id}/items/AAPL')

    # ASSERT (Remove)
    assert remove_response.status_code == 200
    assert WatchlistItem.query.count() == 0