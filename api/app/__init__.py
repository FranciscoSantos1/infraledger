import os
from flask import Flask

from app.config import config_by_name
from app.extensions import db, migrate


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    register_blueprints(app)

    return app

def register_blueprints(app):
    from routes.health import health_bp
    from routes.resources import resources_bp
    from routes.costs import costs_bp
    from routes.insights import insights_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(resources_bp, url_prefix="/api/v1")
    app.register_blueprint(costs_bp, url_prefix="/api/v1")
    app.register_blueprint(insights_bp, url_prefix="/api/v1")