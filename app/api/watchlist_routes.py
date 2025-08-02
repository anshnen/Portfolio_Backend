# app/api/watchlist_routes.py

from flask import Blueprint, jsonify, request
from app.services import watchlist_service

watchlist_bp = Blueprint('watchlist_bp', __name__)

@watchlist_bp.route('/<int:portfolio_id>', methods=['GET'])
def get_watchlists_route(portfolio_id):
    """Get all watchlists for a portfolio."""
    try:
        watchlists = watchlist_service.get_all_watchlists(portfolio_id)
        return jsonify(watchlists), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@watchlist_bp.route('/', methods=['POST'])
def create_watchlist_route():
    """Create a new watchlist."""
    data = request.get_json()
    if not data or 'portfolio_id' not in data or 'name' not in data:
        return jsonify({"error": "Missing portfolio_id or name"}), 400
    try:
        watchlist = watchlist_service.create_watchlist(data['portfolio_id'], data['name'])
        return jsonify({"id": watchlist.id, "name": watchlist.name}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@watchlist_bp.route('/<int:watchlist_id>', methods=['DELETE'])
def delete_watchlist_route(watchlist_id):
    """Delete an entire watchlist."""
    try:
        watchlist_service.delete_watchlist(watchlist_id)
        return jsonify({"message": "Watchlist deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@watchlist_bp.route('/<int:watchlist_id>', methods=['PATCH'])
def rename_watchlist_route(watchlist_id):
    """Rename an existing watchlist."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Missing 'name' in request body"}), 400
    try:
        watchlist = watchlist_service.rename_watchlist(watchlist_id, data['name'])
        return jsonify({"id": watchlist.id, "name": watchlist.name, "message": "Watchlist renamed successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@watchlist_bp.route('/<int:watchlist_id>/items', methods=['POST'])
def add_item_route(watchlist_id):
    """Add an item to a specific watchlist."""
    data = request.get_json()
    if not data or 'ticker' not in data:
        return jsonify({"error": "Missing asset ticker"}), 400
    try:
        item = watchlist_service.add_item_to_watchlist(watchlist_id, data['ticker'])
        return jsonify({"message": "Item added successfully", "asset_id": item.asset_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@watchlist_bp.route('/<int:watchlist_id>/items/<string:ticker>', methods=['DELETE'])
def remove_item_route(watchlist_id, ticker):
    """Remove an item from a watchlist by its ticker symbol."""
    try:
        watchlist_service.remove_item_from_watchlist(watchlist_id, ticker)
        return jsonify({"message": f"Item '{ticker.upper()}' removed successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500