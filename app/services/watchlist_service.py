# app/services/watchlist_service.py

from app.models.models import db, Watchlist, WatchlistItem, Asset, Portfolio
from .market_data_service import MarketDataService

def get_all_watchlists(portfolio_id: int):
    """Retrieves all watchlists for a given portfolio, including their items."""
    watchlists = Watchlist.query.filter_by(portfolio_id=portfolio_id).all()
    result = []
    for wl in watchlists:
        items = [
            {
                "asset_id": item.asset.id,
                "ticker_symbol": item.asset.ticker_symbol,
                "name": item.asset.name,
                "last_price": float(item.asset.last_price) if item.asset.last_price else None
            } for item in wl.items
        ]
        result.append({ "id": wl.id, "name": wl.name, "items": items })
    return result

def create_watchlist(portfolio_id: int, name: str):
    """Creates a new, empty watchlist."""
    portfolio = db.session.get(Portfolio, portfolio_id)
    if not portfolio:
        raise ValueError("Portfolio not found.")
    
    if Watchlist.query.filter_by(portfolio_id=portfolio_id, name=name).first():
        raise ValueError(f"Watchlist with name '{name}' already exists.")

    new_watchlist = Watchlist(name=name, portfolio_id=portfolio_id)
    db.session.add(new_watchlist)
    db.session.commit()
    return new_watchlist

def delete_watchlist(watchlist_id: int):
    """Deletes an entire watchlist and all its associated items."""
    watchlist = db.session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise ValueError("Watchlist not found.")
    
    db.session.delete(watchlist)
    db.session.commit()
    return True

def rename_watchlist(watchlist_id: int, new_name: str):
    """Renames an existing watchlist."""
    watchlist = db.session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise ValueError("Watchlist not found.")
    
    if Watchlist.query.filter(Watchlist.id != watchlist_id, Watchlist.portfolio_id == watchlist.portfolio_id, Watchlist.name == new_name).first():
        raise ValueError(f"A watchlist with the name '{new_name}' already exists.")

    watchlist.name = new_name
    db.session.commit()
    return watchlist

def add_item_to_watchlist(watchlist_id: int, ticker: str):
    """Adds a new asset to a watchlist using "find-or-create" logic."""
    watchlist = db.session.get(Watchlist, watchlist_id)
    if not watchlist:
        raise ValueError("Watchlist not found.")
    
    asset = MarketDataService.find_or_create_asset(ticker)

    if WatchlistItem.query.filter_by(watchlist_id=watchlist_id, asset_id=asset.id).first():
        raise ValueError(f"Asset '{ticker.upper()}' is already in this watchlist.")

    new_item = WatchlistItem(watchlist_id=watchlist_id, asset_id=asset.id)
    db.session.add(new_item)
    db.session.commit()
    
    return new_item

def remove_item_from_watchlist(watchlist_id: int, ticker: str):
    """Removes an item from a watchlist by its ticker symbol."""
    ticker = ticker.upper()
    asset = Asset.query.filter_by(ticker_symbol=ticker).first()
    if not asset:
        raise ValueError(f"Asset with ticker '{ticker}' not found.")

    item = WatchlistItem.query.filter_by(watchlist_id=watchlist_id, asset_id=asset.id).first()
    if not item:
        raise ValueError(f"'{ticker}' not found in this watchlist.")
    
    db.session.delete(item)
    db.session.commit()
    return True
