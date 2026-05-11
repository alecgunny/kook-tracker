import os


def get_database_url():
    url = os.environ.get("DATABASE_URL")
    if url:
        # SQLAlchemy wants postgresql:// not postgres://
        return url.replace("postgres://", "postgresql://", 1)
    return "sqlite:///" + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "app.db"
    )


class Config:
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOG_DIR = os.environ.get("LOG_DIR", ".")
    CLIENT_WAIT_SECONDS = 1
    MAIN_URL = "https://www.worldsurfleague.com"

    # don't allow an event to be created unless we're less than this many
    # days before start date (assuming it hasn't been cancelled or postponed)
    LEAD_DAYS_FOR_EVENT_CREATION = 3
