# tests/test_services/test_watchlist_service.py

import pytest
from app.services import watchlist_service
from app.models.models import User, Portfolio, Watchlist, Asset, WatchlistItem
from tests.data.mock_api_data import MOCK_AAPL_DATA

def test_create_watchlist_success(db):
    """
    GIVEN a portfolio
    WHEN create_watchlist is called with a unique name
    THEN a new Watchlist should be created
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    db.session.add_all([user, portfolio])
    db.session.commit()

    # ACT
    watchlist = watchlist_service.create_watchlist(portfolio.id, "My Tech Stocks")

    # ASSERT
    assert watchlist is not None
    assert watchlist.name == "My Tech Stocks"
    assert Watchlist.query.count() == 1

def test_add_item_to_watchlist_creates_new_asset(db, mocker):
    """
    GIVEN an empty assets table and a watchlist
    WHEN add_item_to_watchlist is called with a new ticker
    AND the MarketDataService is mocked
    THEN a new Asset should be created and added to the watchlist
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    watchlist = Watchlist(name="Test Watchlist", portfolio=portfolio)
    db.session.add_all([user, portfolio, watchlist])
    db.session.commit()
    
    # Mock the find_or_create_asset to simulate creating a new asset
    mocker.patch(
        'app.services.market_data_service.MarketDataService.find_or_create_asset',
        return_value=Asset(ticker_symbol="AAPL", name="Apple Inc")
    )

    # ACT
    item = watchlist_service.add_item_to_watchlist(watchlist.id, "AAPL")

    # ASSERT
    assert item is not None
    assert Asset.query.count() == 1
    assert WatchlistItem.query.count() == 1
    assert WatchlistItem.query.first().asset.ticker_symbol == "AAPL"

def test_add_existing_item_to_watchlist_fails(db):
    """
    GIVEN an asset that is already in a watchlist
    WHEN add_item_to_watchlist is called with the same ticker
    THEN a ValueError should be raised
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    watchlist = Watchlist(name="Test Watchlist", portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc")
    item = WatchlistItem(watchlist=watchlist, asset=asset)
    db.session.add_all([user, portfolio, watchlist, asset, item])
    db.session.commit()

    # ACT & ASSERT
    with pytest.raises(ValueError, match="'AAPL' is already in this watchlist"):
        watchlist_service.add_item_to_watchlist(watchlist.id, "AAPL")

def test_remove_item_from_watchlist_by_ticker(db):
    """
    GIVEN a watchlist with an item
    WHEN remove_item_from_watchlist is called with the item's ticker
    THEN the item should be removed
    """
    # ARRANGE
    user = User(username="test", email="test@test.com", password_hash="123")
    portfolio = Portfolio(name="Test Portfolio", user=user)
    watchlist = Watchlist(name="Test Watchlist", portfolio=portfolio)
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc")
    item = WatchlistItem(watchlist=watchlist, asset=asset)
    db.session.add_all([user, portfolio, watchlist, asset, item])
    db.session.commit()
    
    assert WatchlistItem.query.count() == 1

    # ACT
    result = watchlist_service.remove_item_from_watchlist(watchlist.id, "AAPL")

    # ASSERT
    assert result is True
    assert WatchlistItem.query.count() == 0