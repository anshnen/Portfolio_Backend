# tests/test_services/test_watchlist_service.py

import pytest
from app.services import watchlist_service
from app.models.models import User, Portfolio, Watchlist, Asset, WatchlistItem, AssetType

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
    
    # FIX: Mock the service to return a valid Asset with the required asset_type and an id
    mock_asset = Asset(id=1, ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK)
    mocker.patch(
        'app.services.market_data_service.MarketDataService.find_or_create_asset',
        return_value=mock_asset
    )

    # ACT
    item = watchlist_service.add_item_to_watchlist(watchlist.id, "AAPL")

    # ASSERT
    assert item is not None
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
    # FIX: Added the required 'asset_type' field.
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK)
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
    # FIX: Added the required 'asset_type' field.
    asset = Asset(ticker_symbol="AAPL", name="Apple Inc", asset_type=AssetType.STOCK)
    item = WatchlistItem(watchlist=watchlist, asset=asset)
    db.session.add_all([user, portfolio, watchlist, asset, item])
    db.session.commit()
    
    assert WatchlistItem.query.count() == 1

    # ACT
    result = watchlist_service.remove_item_from_watchlist(watchlist.id, "AAPL")

    # ASSERT
    assert result is True
    assert WatchlistItem.query.count() == 0