import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "media.db")


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me")
    APP_NAME = os.getenv("APP_NAME", "My App")
    TAILSCALE_IP = os.getenv("TAILSCALE_IP", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    PROFILES = os.getenv("PROFILES", "Default")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MUSICBRAINZ_USER_AGENT = os.getenv(
        "MUSICBRAINZ_USER_AGENT", "media-tracker/1.0 ( contact@example.com )"
    )
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
    RAWG_API_KEY = os.getenv("RAWG_API_KEY", "")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
