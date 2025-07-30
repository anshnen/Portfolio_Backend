from app.models.models import db, Watchlist, WatchlistItem, Asset, Portfolio
from .market_data_service import MarketDataService

def get_all_watchlists(portfolio_id: int):
    """Retrieves all watchlists for a given portfolio, including their items."""
    watchlists = Watchlist.query.filter_by(portfolio_id=portfolio_id).all()
    result = []
    for wl in watchlists:
        items = []
        for item in wl.items:
            asset = item.asset
            items.append({
                "asset_id": asset.id,
                "ticker_symbol": asset.ticker_symbol,
                "name": asset.name,
                "last_price": float(asset.last_price) if asset.last_price else None
            })
        result.append({
            "id": wl.id,
            "name": wl.name,
            "items": items
        })
    return result

def create_watchlist(portfolio_id: int, name: str):
    """Creates a new, empty watchlist."""
    portfolio = Portfolio.query.get(portfolio_id)
    if not portfolio:
        raise ValueError("Portfolio not found.")
    
    existing = Watchlist.query.filter_by(portfolio_id=portfolio_id, name=name).first()
    if existing:
        raise ValueError(f"Watchlist with name '{name}' already exists.")

    new_watchlist = Watchlist(name=name, portfolio_id=portfolio_id)
    db.session.add(new_watchlist)
    db.session.commit()
    return new_watchlist

def add_item_to_watchlist(watchlist_id: int, ticker: str):
    """
    Adds a new asset to a watchlist by its ticker symbol.
    Implements "find-or-create" logic for assets.
    """
    watchlist = Watchlist.query.get(watchlist_id)
    if not watchlist:
        raise ValueError("Watchlist not found.")
    
    ticker = ticker.upper()
    
    # 1. FIND: Check if the asset already exists in our database
    asset = Asset.query.filter_by(ticker_symbol=ticker).first()

    # 2. CREATE (if not found)
    if not asset:
        print(f"Asset '{ticker}' not in DB. Fetching from external API...")
        asset_info = MarketDataService.fetch_asset_info(ticker)
        
        if not asset_info:
            raise ValueError(f"Could not find a valid asset for ticker '{ticker}'.")
        
        # Create a new Asset record
        asset = Asset(
            ticker_symbol=asset_info['ticker_symbol'],
            name=asset_info['name'],
            asset_type=asset_info['asset_type'],
            last_price=asset_info['last_price'],
            previous_close_price=asset_info['previous_close_price']
        )
        db.session.add(asset)
        # We commit here to get an ID for the new asset before creating the watchlist item
        db.session.commit()
        print(f"New asset '{asset.name}' created and added to the database.")

    # 3. LINK
    existing_item = WatchlistItem.query.filter_by(watchlist_id=watchlist_id, asset_id=asset.id).first()
    if existing_item:
        raise ValueError(f"Asset '{ticker}' is already in this watchlist.")

    new_item = WatchlistItem(watchlist_id=watchlist_id, asset_id=asset.id)
    db.session.add(new_item)
    db.session.commit()
    
    return new_item

def remove_item_from_watchlist(watchlist_id: int, asset_id: int):
    """Removes an item from a watchlist."""
    item = WatchlistItem.query.filter_by(watchlist_id=watchlist_id, asset_id=asset_id).first()
    if not item:
        raise ValueError("Item not found in this watchlist.")
    
    db.session.delete(item)
    db.session.commit()
    return True