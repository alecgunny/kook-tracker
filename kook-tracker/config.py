import os


def get_database_url():
    if os.environ.get("RDS_HOSTNAME") is not None:
        return (
            "postgresql://{RDS_USERNAME}:{RDS_PASSWORD}"
            "@{RDS_HOSTNAME}:{RDS_PORT}/{RDS_DB_NAME}".format(**os.environ)
        )
    else:
        return "sqlite:///" + os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "app.db"
        )


class Config:
    SECRET_KEY = os.environ.get("RDS_PASSWORD", "ruby-tuesday")
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOG_DIR = os.environ.get("LOG_DIR", ".")
    CLIENT_WAIT_SECONDS = 1
    MAIN_URL = "https://www.worldsurfleague.com"

    # don't allow an event to be created unless we're less than this many
    # days before start date (assuming it hasn't been cancelled or postponed)
    LEAD_DAYS_FOR_EVENT_CREATION = 3
