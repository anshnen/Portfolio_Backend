# app/api/order_routes.py

from flask import Blueprint, jsonify, request
from app.services.order_service import OrderService

order_bp = Blueprint('order_bp', __name__)

@order_bp.route('/', methods=['POST'])
def place_order_route():
    """
    Endpoint to place a buy or sell order.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request body"}), 400
    
    try:
        # In a real app with authentication, user_id would come from the session/token
        user_id = 1 
        transaction = OrderService.place_order(user_id, data)
        return jsonify({
            "message": f"{data['order_type'].capitalize()} order completed successfully.",
            "transactionId": transaction.id
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500