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

        # Force an absolute path using app.instance_path for SQLite
        instance_folder_path = app.instance_path
        db_name = 'app.db' # Fixed name
        db_path = os.path.join(instance_folder_path, db_name)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
        # Print this only if FLASK_DEBUG or a specific debug flag is on, to avoid noise
        if app.debug:
            print(f"INFO: Using absolute SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your_default_jwt_secret_key')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db) # Flask-Migrate uses the app config for DB URI
    jwt.init_app(app)

    # Import models here to ensure they are registered with SQLAlchemy
    from app import models # noqa: F401

    # Create instance folder if it doesn't exist (Flask usually does this)
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
        if app.debug:
            print(f"INFO: Created instance folder at {app.instance_path}")

    # Register Blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.routes.document_type import dt_bp
    app.register_blueprint(dt_bp, url_prefix='/api/document-types')

    from app.routes.document import doc_bp
    app.register_blueprint(doc_bp, url_prefix='/api/documents')

    from app.routes.consent_request import cr_bp
    app.register_blueprint(cr_bp, url_prefix='/api/consent-requests')

    @app.route('/hello')
    def hello():
        return "Hello, CMS!"

    # The db.create_all() block has been removed.
    # Schema creation and updates will now be handled by Flask-Migrate.

    return app
