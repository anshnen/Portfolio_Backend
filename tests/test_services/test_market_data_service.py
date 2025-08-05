# tests/test_services/test_market_data_service.py

import pytest
from decimal import Decimal
from app.services.market_data_service import MarketDataService
from app.models.models import Asset, AssetType
from tests.data.mock_api_data import MOCK_AAPL_DATA, MOCK_RELIANCE_DATA

def test_find_or_create_asset_creates_new_asset(db, mocker):
    """
    GIVEN a ticker symbol that does not exist in the database
    WHEN find_or_create_asset is called
    AND the external API call is mocked
    THEN a new Asset should be created and saved to the database with the correct data
    """
    # ARRANGE
    # Mock the external API call to prevent a real network request
    mocker.patch(
        'app.services.market_data_service.MarketDataService.get_price_from_source',
        return_value=MOCK_RELIANCE_DATA
    )
    
    # ACT
    asset = MarketDataService.find_or_create_asset("RELIANCE.NS")
    
    # ASSERT
    assert asset is not None
    assert asset.ticker_symbol == "RELIANCE.NS"
    assert asset.name == "Reliance Industries Limited"
    assert asset.sector == "Energy"
    
    # Verify it was actually saved to the database
    asset_from_db = Asset.query.filter_by(ticker_symbol="RELIANCE.NS").first()
    assert asset_from_db is not None
    assert asset_from_db.id == asset.id

def test_find_or_create_asset_finds_existing_asset(db, mocker):
    """
    GIVEN a ticker symbol that already exists in the database
    WHEN find_or_create_asset is called
    THEN the existing Asset should be returned without creating a new one
    """
    # ARRANGE
    existing_asset = Asset(
        ticker_symbol="AAPL",
        name="Apple Inc",
        asset_type=AssetType.STOCK,
        last_price=Decimal("150.00")
    )
    db.session.add(existing_asset)
    db.session.commit()
    
    # Mock the external API call to ensure it's not being called unnecessarily
    mock_api_call = mocker.patch(
        'app.services.market_data_service.MarketDataService.get_price_from_source'
    )

    # ACT
    asset = MarketDataService.find_or_create_asset("AAPL")

    # ASSERT
    assert asset is not None
    assert asset.id == existing_asset.id
    assert asset.name == "Apple Inc"
    
    # Verify that the external API was not called
    mock_api_call.assert_not_called()
    
    # Verify no new asset was created
    all_assets = Asset.query.all()
    assert len(all_assets) == 1

def test_get_asset_details_logic(db, mocker):
    """
    GIVEN a ticker symbol
    WHEN get_asset_details is called
    AND dependent service calls are mocked
    THEN it should return a dictionary with the correct, comprehensive structure
    """
    # ARRANGE
    # We can use a mock object to simulate the Asset model
    mock_asset = Asset(
        id=1,
        ticker_symbol="AAPL",
        name="Apple Inc.",
        last_price=MOCK_AAPL_DATA['last_price'],
        sector=MOCK_AAPL_DATA['sector'],
        market_cap=MOCK_AAPL_DATA['market_cap']
    )
    
    # Mock the service methods that this function depends on
    mocker.patch(
        'app.services.market_data_service.MarketDataService.find_or_create_asset',
        return_value=mock_asset
    )
    mocker.patch(
        'app.services.market_data_service.MarketDataService.update_historical_data',
        return_value=None # We don't need it to do anything for this test
    )
    mocker.patch(
        'app.models.models.HistoricalPrice.query' # Mock the database query for historical data
    )

    # ACT
    details = MarketDataService.get_asset_details("AAPL")

    # ASSERT
    assert details is not None
    assert details['ticker_symbol'] == "AAPL"
    assert details['name'] == "Apple Inc."
    assert "fundamentals" in details
    assert "technicals" in details
    assert "historical_data" in details
    assert details['fundamentals']['sector'] == "Technology"
    assert details['fundamentals']['market_cap'] == 3000000000000