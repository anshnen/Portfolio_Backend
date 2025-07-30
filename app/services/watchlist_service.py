from app.models.models import db, Watchlist, WatchlistItem, Asset, Portfolio

def get_all_watchlists(portfolio_id: int):
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
    watchlist = Watchlist.query.get(watchlist_id)
    if not watchlist:
        raise ValueError("Watchlist not found.")
    
    asset = Asset.query.filter_by(ticker_symbol=ticker.upper()).first()
    if not asset:
        raise ValueError(f"Asset with ticker '{ticker}' not found.")

    existing_item = WatchlistItem.query.filter_by(watchlist_id=watchlist_id, asset_id=asset.id).first()
    if existing_item:
        raise ValueError(f"Asset '{ticker}' is already in this watchlist.")

    new_item = WatchlistItem(watchlist_id=watchlist_id, asset_id=asset.id)
    db.session.add(new_item)
    db.session.commit()
    return new_item

def remove_item_from_watchlist(watchlist_id: int, asset_id: int):
    item = WatchlistItem.query.filter_by(watchlist_id=watchlist_id, asset_id=asset_id).first()
    if not item:
        raise ValueError("Item not found in this watchlist.")
    
    db.session.delete(item)
    db.session.commit()
    return True