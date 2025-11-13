import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from config import config
from models import db
from blueprints.auth import auth_bp
from blueprints.products import products_bp
from blueprints.cart import cart_bp
from auth_gateway import init_auth_gateway

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))
    
    # Validate required configuration after loading (fail fast with clear message)
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Provide it via environment (recommended in Kubernetes) or a .env file."
        )
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Initialize auth gateway that verifies JWT for protected routes
    init_auth_gateway(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Create tables
    with app.app_context():
        none = None
        # db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
