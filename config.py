import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
  SECRET_KEY = os.environ.get('RDS_PASSWORD', 'ruby-tuesday')
  SQLALCHEMY_DATABASE_URI = os.environ.get('RDS_HOSTNAME') or \
    'sqlite:///' + os.path.join(basedir, 'app.db')
  SQLALCHEMY_TRACK_MODIFICATIONS = False

  LOG_DIR = os.environ.get('LOG_DIR', '.')
  CLIENT_WAIT_SECONDS = 1
  MAIN_URL = 'https://www.worldsurfleague.com'