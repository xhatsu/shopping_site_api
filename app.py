import os
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
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
    
    # Initialize CORS with allowed origins from environment
    cors_origins = os.getenv('CORS_ORIGINS', 'http://158.178.228.216:3000').split(',')
    cors_origins = [origin.strip() for origin in cors_origins]
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Initialize auth gateway that verifies JWT for protected routes
    init_auth_gateway(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    
    # Swagger UI setup
    swagger_url = '/api/docs'
    api_url = '/openapi.yaml'
    swagger_ui_blueprint = get_swaggerui_blueprint(
        swagger_url,
        api_url,
        config={'app_name': 'Shopping Site API'}
    )
    app.register_blueprint(swagger_ui_blueprint, url_prefix=swagger_url)
    
    # Serve OpenAPI spec
    @app.route('/openapi.yaml')
    def openapi_spec():
        import yaml
        with open('openapi.yaml', 'r') as f:
            spec = yaml.safe_load(f)
        return spec
    
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
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
