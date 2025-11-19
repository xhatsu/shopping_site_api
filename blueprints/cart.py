from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, CartItem, Product, User

cart_bp = Blueprint('cart', __name__, url_prefix='/api/cart')

@cart_bp.route('', methods=['GET'])
@jwt_required()
def get_cart():
    """Get user's cart items"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    total_price = sum(item.quantity * item.product.price for item in cart_items)
    
    return jsonify({
        'items': [item.to_dict() for item in cart_items],
        'total_items': len(cart_items),
        'total_price': total_price
    }), 200

@cart_bp.route('/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Add product to cart"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': f'User with id {user_id} not found'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('product_id'):
        return jsonify({'error': 'Missing product_id'}), 400
    
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': f'Product with id {data["product_id"]} not found'}), 404
    
    quantity = int(data.get('quantity', 1))
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be greater than 0'}), 400
    
    if product.stock < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    cart_item = CartItem.query.filter_by(
        user_id=user_id,
        product_id=product.id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product.id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Product added to cart',
        'item': cart_item.to_dict()
    }), 201

@cart_bp.route('/item/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(item_id):
    """Update cart item quantity"""
    user_id = get_jwt_identity()
    cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first_or_404()
    data = request.get_json()
    
    quantity = int(data.get('quantity', 1))
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be greater than 0'}), 400
    
    if cart_item.product.stock < quantity:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    cart_item.quantity = quantity
    db.session.commit()
    
    return jsonify({
        'message': 'Cart item updated',
        'item': cart_item.to_dict()
    }), 200

@cart_bp.route('/item/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    """Remove item from cart"""
    user_id = get_jwt_identity()
    cart_item = CartItem.query.filter_by(id=item_id, user_id=user_id).first_or_404()
    
    db.session.delete(cart_item)
    db.session.commit()
    
    return jsonify({'message': 'Item removed from cart'}), 200

@cart_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Clear user's entire cart"""
    user_id = get_jwt_identity()
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return jsonify({'message': 'Cart cleared'}), 200
