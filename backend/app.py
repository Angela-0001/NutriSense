"""
NutriSense Flask Application
app.py — Main entry point

Run:
    pip install -r requirements.txt
    python app.py

The app auto-seeds the database on first run.
Demo login: demo@nutrisense.in / demo123
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from database.models import db
from database.seed_data import seed_database

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)

    # ── CONFIG ─────────────────────────────────────────────────────────
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'nutrisense.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nutrisense-dev-secret-2024')
    app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'nutrisense-jwt-secret-2024')

    # ── EXTENSIONS ─────────────────────────────────────────────────────
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── DATABASE INIT ──────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        seed_database(app, db)

    # ── REGISTER BLUEPRINTS ────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.foods import foods_bp
    from routes.logs import logs_bp
    from routes.analysis import analysis_bp
    from routes.meal_plan import meal_plan_bp
    from routes.vision import vision_bp
    from routes.dataset_gen import dataset_bp

    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(foods_bp,     url_prefix='/api/foods')
    app.register_blueprint(logs_bp,      url_prefix='/api/logs')
    app.register_blueprint(analysis_bp,  url_prefix='/api/analysis')
    app.register_blueprint(meal_plan_bp, url_prefix='/api/meal-plan')
    app.register_blueprint(vision_bp,    url_prefix='/api/vision')
    app.register_blueprint(dataset_bp,   url_prefix='/api/dataset')

    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'app': 'NutriSense'}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
