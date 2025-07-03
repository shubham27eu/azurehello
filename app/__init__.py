import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=None):
    """Application Factory Function"""
    app = Flask(__name__)

    # Configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        # Default configuration if no config_class is provided
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../instance/app.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_default_jwt_secret_key')
        # Configure JWT settings if needed, e.g., token expiration
        # app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Import models here to ensure they are registered with SQLAlchemy
    # before Alembic tries to access db.metadata via current_app
    from app import models

    # Create instance folder if it doesn't exist
    instance_path = app.instance_path
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"Created instance folder at {instance_path}")


    # Register Blueprints (example, will be defined later)
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.routes.document_type import dt_bp
    app.register_blueprint(dt_bp, url_prefix='/api/document-types')

    from app.routes.document import doc_bp
    app.register_blueprint(doc_bp, url_prefix='/api/documents')

    from app.routes.consent_request import cr_bp
    app.register_blueprint(cr_bp, url_prefix='/api/consent-requests')

    # A simple test route
    @app.route('/hello')
    def hello():
        return "Hello, CMS!"

    return app
