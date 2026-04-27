import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from config import configs

load_dotenv()

db = SQLAlchemy()


def _ensure_sqlite_dir(uri: str) -> None:
    """Create the parent directory for a SQLite file URI if it doesn't exist.

    Without this, db.create_all() fails on first boot when DATABASE_URL
    points at a path whose dir hasn't been created yet (e.g. data/media.db).
    """
    if not uri.startswith("sqlite:"):
        return
    path = uri.split(":///", 1)[-1]
    if not path or path == ":memory:":
        return
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def create_app(config_name=None):
    """App factory. Reads FLASK_ENV to select config, wires up db, blueprints, and error handlers."""
    app = Flask(__name__, instance_relative_config=True)

    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    app.config.from_object(configs[config_name])

    _ensure_sqlite_dir(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    db.init_app(app)

    # Side-effect import: registers model classes with SQLAlchemy metadata
    from . import models  # noqa: F401

    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_globals():
        from app.utils.helpers import current_profile
        profiles = [p.strip() for p in app.config["PROFILES"].split(",")]
        return {"current_profile": current_profile(), "profiles": profiles}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()

    return app
