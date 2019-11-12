from app import db


heat_results = db.Table(
  'heat_results',
  db.Column('heat_id', db.Integer, db.ForeignKey('heat.id'), primary_key=True),
  db.Column('athlete_id', db.Integer, db.ForeignKey('athlete.id'), primary_key=True),
  db.Column('score', db.Numeric(2,2), default=None))


class Heat(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  completed = db.Column(db.Boolean, default=False)
  round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
  athletes = db.relationship('Athlete', secondary=heat_results, lazy='subquery',
    backref=db.backref('heats', lazy=True))


class Round(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  completed = db.Column(db.Boolean, default=False)
  number = db.Column(db.Integer)
  event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
  heats = db.relationship('Heat', backref='round', lazy='dynamic')


class Event(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
  completed = db.Column(db.Boolean, default=False)
  year = db.Column(db.Integer, db.ForeignKey('season.year'))
  rounds = db.relationship('Round', backref='event', lazy='dynamic')


class Season(db.Model):
  year = db.Column(db.Integer, primary_key=True)
  events = db.relationship('Event', backref='season', lazy='dynamic')


class Athlete(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
