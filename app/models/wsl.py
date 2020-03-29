from app import db
from app import parsers
from app.models import mixins
from config import Config


class HeatResult(db.Model):
  heat_id = db.Column(
    db.Integer,
    db.ForeignKey('heat.id'),
    primary_key=True
  )
  athlete_id = db.Column(
    db.Integer,
    db.ForeignKey('athlete.id'),
    primary_key=True
  )
  score = db.Column(db.Numeric(2, 2), default=None)

  heat = db.relationship(
    'Heat', backref=db.backref('heats', lazy=True))
  athlete = db.relationship(
    'Athlete', backref=db.backref('athletes', lazy=True))


class Heat(mixins.Updatable, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  completed = db.Column(db.Boolean, default=False)
  status = db.Column(db.Integer, default=0)
  round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
  athletes = db.relationship(
    'HeatResult',
    backref='result_heat'
  )

  @classmethod
  def create(cls, **kwargs):
    obj = cls(completed=False, **kwargs)
    obj.update()
    return obj

  def _do_update(self):
    status, scores = parsers.get_heat_data(self.round.url, self.id)
    self.status = status

    for athlete_name, score in scores.items():
      athlete = Athlete.query.filter_by(name=athlete_name).first()
      if athlete is None and self.status > 0:
        # only add athlete to database if heat has started since sometimes
        # there can be placeholder names while heat is upcoming
        athlete = Athlete(name=athlete_name)
        db.session.add(athlete)
        db.session.commit() # need a commit for heat result query
      elif athlete is None:
        continue

      # try to update an existing heat result if it exists, otherwise
      # create a new one
      heat_result = HeatResult.query.filter_by(
        heat=self, athlete=athlete).first()
      if heat_result is None:
        heat_result = HeatResult(athlete=athlete)
        self.athletes.append(heat_result)
        db.session.add(heat_result)

      # update the heat result score
      heat_result.score = score
    self.completed = status == 2


class Round(mixins.Updatable, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  completed = db.Column(db.Boolean, default=False)
  number = db.Column(db.Integer)
  event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
  heats = db.relationship('Heat', backref='round', lazy='dynamic')

  @property
  def url(self):
    return parsers.get_round_url(self)

  @classmethod
  def create(cls, **kwargs):
    obj = cls(completed=False, **kwargs)
    heat_ids = parsers.get_heat_ids(obj.url)
    for id in heat_ids:
      db.session.add(Heat.create(id=id, round=obj))
    obj.completed = all([heat.completed for heat in obj.heats])
    return obj

  def _do_update(self):
    # some custom logic that will only update a heat if the one before it is
    # completed or ongoing
    _do_break = False
    for n, heat in enumerate(self.heats):
      # heat is not completd and we haven't triggered a break yet
      if not heat.update() and not _do_break:
        # heat is either upcoming, which means the next heat doesn't need
        # updating, or we're on the last heat, so break in order
        # to avoid the loop else clause
        if heat.status == 0 or n == (len(self.heats)-1):
          break
        else:
          # update the next heat in the case of side-by-side heats
          _do_break = True

      elif _do_break:
        break

    else:
      # we never triggered a break i.e. all heats are completed
      self.completed = True


class Event(mixins.Updatable, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
  completed = db.Column(db.Boolean, default=False)
  year = db.Column(db.Integer, db.ForeignKey('season.year'))
  rounds = db.relationship('Round', backref='event', lazy='dynamic')

  @property
  def url(self):
    return Config.MAIN_URL + '/events/{}/mct/{}/{}'.format(
      self.year, self.id, self.name)

  @classmethod
  def create(cls, **kwargs):
    obj = cls(**kwargs)
    try:
      round_ids = parsers.get_round_ids(obj.url + '/results')
    except parsers.EventNotReady:
      raise parsers.EventNotReady(
        'No valid round links for event {}'.format(obj.name)
      )

    with db.session.no_autoflush:
      for n, round_id in enumerate(round_ids):
        db.session.add(Round.create(id=round_id, number=n, event=obj))
    obj.completed = all([round_.completed for round_ in obj.rounds])
    return obj

  def _do_update(self):
    for round_ in self.rounds:
      # update returns completion status, so if round hasn't completed after
      # its own update, stop because there's no sense updating rounds that
      # haven't begun yet
      if not round_.update():
        break
    else:
      # loop completed without breaking: means all our rounds have completed
      self.completed = True


class Season(db.Model):
  year = db.Column(db.Integer, primary_key=True)
  events = db.relationship('Event', backref='season', lazy='dynamic')


class Athlete(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
  heats = db.relationship(
    'HeatResult',
    backref='result_athlete'
  )
