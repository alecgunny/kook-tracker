import logging
import os
from datetime import datetime

from client import Client
from config import Config
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

config = Config()
app = Flask(__name__)
app.config.from_object(config)

if not os.path.exists(config.LOG_DIR):
    os.makedirs(config.LOG_DIR)

logging.basicConfig(
    filename=os.path.join(config.LOG_DIR, "app.log"), level=logging.DEBUG
)

db = SQLAlchemy(app)
migrate = Migrate(app, db, compare_type=True)
client = Client(app)

from app import models, parsers, routes  # noqa

# make this season if it doesn't already exist
# now = datetime.now()
# year = now.year
# with app.app_context():
#     season = models.wsl.Season.query.filter_by(year=year).first()
#     if season is None:
#         app.logger.info(f"Initializing {year} season")
#         season = models.wsl.Season.create(year=year)
#     else:
#         season_url = parsers.get_season_url(season)
#         event_metadata = parsers.get_event_data_from_season_homepage(
#             season_url
#         )
#         for metadata in event_metadata:
#             if metadata["status"] in ("standby", "live"):
#                 id, event_name = metadata["link"].split("/")[-3:-1]
#                 event = models.wsl.Event.query.filter_by(id=id).first()
#                 if event is None:
#                     app.logger.info(f"Initializing event {event_name}")
#                     stat_id = metadata["id"]
#                     event = models.wsl.Event.create(
#                         name=event_name, id=id, stat_id=stat_id, year=year
#                     )
#                     season.events.append(event)
#                     db.session.add(event)

#                 if not event.completed:
#                     event.update()
#                 db.session.commit()
#                 break
#         else:
#             app.logger.info("No events to create or update")
