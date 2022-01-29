import logging
import os

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

from app import models, routes  # noqa
