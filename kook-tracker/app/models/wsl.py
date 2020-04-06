from app import db
from app import parsers
from app.models import mixins
from config import Config

import datetime


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

  # store scores as ints in the range [0, 60]
  # calculate float value at read time by
  # dividing by 6
  score = db.Column(db.Integer, default=None)

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

      # create athlete if they don't exist
      # note that we don't need to worry about placeholder names since
      # the parser function takes care of checking for these first
      if athlete is None:
        athlete = Athlete(name=athlete_name)
        db.session.add(athlete)
        db.session.commit() # need a commit for heat result query

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
        # trigger a break after updating next heat, for side-by-side heats
        _do_break = True
        
        # unless current heat is either upcoming, which means the next heat
        # doesn't need updating, or we're on the last heat, which means break
        # now instead in order to avoid the loop else clause
        if heat.status == 0 or n == (len(self.heats)-1):
          break

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
    return parsers.get_event_url(self)

  @classmethod
  def create(cls, **kwargs):
    obj = cls(**kwargs)

    # first verify that status is ok and that we're close enough to the
    # event to warrant building it
    status, start_date = parsers.get_event_data_from_event_homepage(obj.url)
    if status in ('canceled', 'postponed'):
      raise parsers.EventNotReady(
        'Status for event {} is currently {}'.format(
          obj.name, status
      ))
    elif ((
        datetime.datetime.now() +
          datetime.timedelta(days=Config.LEAD_DAYS_FOR_EVENT_CREATION)
        ) < start_date):
      raise parsers.EventNotReady(
        'Start date for event {} is {} days away, stopping creation'.format(
          obj.name, (start_date - datetime.datetime.now()).days)
      )

    # double check that event is ready to be scraped by making sure that
    # all the rounds have valid links
    try:
      round_ids = parsers.get_round_ids(obj.url + '/results')
    except parsers.EventNotReady:
      raise parsers.EventNotReady(
        'No valid round links for event {}'.format(obj.name)
      )

    # initialize all the internal rounds and heats
    with db.session.no_autoflush:
      for n, round_id in enumerate(round_ids):
        db.session.add(Round.create(id=round_id, number=n, event=obj))

    # if this is an event from the past, we can set it completed up front
    obj.completed = all([round_.completed for round_ in obj.rounds])
    return obj

  @property
  def results(self):
    csv_string = "RoundNum,HeatNum,AthleteName,Score"
    for i, round_ in enumerate(self.rounds):
      for j, heat in enumerate(round_.heats):
        for athlete in heat.athletes:
          csv_string += "\n{},{},{},{}".format(
            i, j, athlete.athlete.name, round(athlete.score / 6, 2)
          )
    return csv_string

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

  @property
  def url(self):
    return parsers.get_season_url(self)

  @classmethod
  def create(cls, **kwargs):
    assert 'year' in kwargs
    if kwargs['year'] > datetime.datetime.now().year:
      raise ValueError(
        'Cannot create season for future year {}'.format(kwargs['year'])
      )

    obj = cls(**kwargs)
    for event_name, event_id in parsers.get_event_ids(obj.url).items():
      try:
        db.session.add(Event.create(name=event_name, id=event_id, season=obj))
      except parsers.EventNotReady:
        continue
    return obj



class Athlete(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(128))
  heats = db.relationship(
    'HeatResult',
    backref='result_athlete'
  )
