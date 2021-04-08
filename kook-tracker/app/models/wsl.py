import datetime
import re

from app import Config, app, db, parsers
from app.models import mixins


class HeatResult(db.Model):
    heat_id = db.Column(db.Integer, db.ForeignKey("heat.id"), primary_key=True)
    athlete_id = db.Column(
        db.Integer,
        db.ForeignKey("athlete.id"),
        # primary_key=True
    )

    index = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Numeric(4, 2), default=None)

    heat = db.relationship("Heat", backref=db.backref("heats", lazy=True))
    athlete = db.relationship(
        "Athlete", backref=db.backref("athletes", lazy=True)
    )


def _is_placeholder_athlete_name(athlete_name):
    # probably overkill on precision but whatever
    regexs = [
        "Round of [0-9]{1,2}, Heat [0-9]{1,2} winner",
        "finals, Heat [0-9]{1,2} winner$",
        "Event seed #[0-9]{1,2}",
        "Round seed #[0-9]{1,2}",
    ]
    if any([re.search(r, athlete_name) is not None for r in regexs]):
        return True
    return False


class Heat(mixins.Updatable, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    completed = db.Column(db.Boolean, default=False)
    status = db.Column(db.Integer, default=0)
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"))
    athletes = db.relationship("HeatResult", backref="result_heat")

    @classmethod
    def create(cls, **kwargs):
        obj = cls(completed=False, **kwargs)
        obj.update()
        return obj

    def _do_update(self):
        status, scores = parsers.get_heat_data(self.round.url, self.id)
        self.status = status

        for index, (athlete_name, score) in enumerate(scores):
            # if we're being reported a placeholder athlete name,
            # then make sure that the heat hasn't started yet. If it has,
            # we need to investigate
            if _is_placeholder_athlete_name(athlete_name) and status != 0:
                msg = "Still using placeholder name {} in ongoing heat {}".format(
                    athlete_name, self.id
                )
                app.logger.warn(msg)
                heat_result = HeatResult.query.filter_by(heat=self, index=index)

                try:
                    athlete = heat_result.first().athlete
                except AttributeError:
                    # case 1: there's no existing entry, so just move on and
                    # pretend this never happend
                    continue

                # case 2: that heat result has a placeholder name attached to it
                # delete it and move on
                if _is_placeholder_athlete_name(athlete.name):
                    msg = "Removing placeholder heat result from heat {}".format(
                        self.id
                    )
                    app.logger.warn(msg)
                    heat_result.delete()
                    continue
                # case 3: that heat used to have a real athete associated
                # with it. I guess keep it for now?
                else:
                    athlete_name = athlete.name

            # create athlete if they don't exist. Note that his means
            # we will create some placeholder athletes, but
            # they won't have any heat results after things get updated
            athlete = Athlete.query.filter_by(name=athlete_name).first()
            if athlete is None:
                athlete = Athlete(name=athlete_name)
                db.session.add(athlete)

            # index heat result by the heat and their order in the heat
            # this way when rounds update from some TBD placeholder to
            # a real athlete name we can update the athlete name accordingly
            # the cost of this is having some placeholder athlete names in
            # our athlete db but that seems like a small price to pay
            heat_result = HeatResult.query.filter_by(
                heat=self, index=index
            ).first()

            # first case: this heat result hasn't been created yet
            # instantiate it and add it to our session
            if heat_result is None:
                heat_result = HeatResult(index=index, athlete=athlete)
                self.athletes.append(heat_result)
                db.session.add(heat_result)
            else:
                # second case: the heat has been created but the athlete
                # being used to instantiate is being updated
                if heat_result.athlete.name != athlete_name:
                    # if this is not because the instantiated athlete was
                    # a placeholder, we won't do this automatically, but
                    # will leave it to you to do manually if you think this
                    # is correct
                    if not _is_placeholder_athlete_name(heat_result.athlete.name):
                        msg = (
                            "Athlete {} is trying to be replaced by athlete {} "
                            "in heat {}. If this is desired, consider doing it "
                            "manually".format(
                                heat_result.athlete.name, athlete_name, self.id
                            )
                        )
                        raise ValueError(msg)

                    # updat the heat result athlete
                    heat_result.athlete = athlete

            # update the heat result score
            heat_result.score = score
        self.completed = status == 2


class Round(mixins.Updatable, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    completed = db.Column(db.Boolean, default=False)
    number = db.Column(db.Integer)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"))
    heats = db.relationship("Heat", backref="round", lazy="dynamic")

    @property
    def url(self):
        return parsers.get_round_url(self)

    @property
    def sorted_heats(self):
        return sorted(self.heats, key=lambda heat: heat.id)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(completed=False, **kwargs)
        heat_ids = parsers.get_heat_ids(obj.url)
        for id in heat_ids:
            db.session.add(Heat.create(id=id, round=obj))
        obj.completed = all([heat.completed for heat in obj.heats])
        return obj

    def _do_update(self):
        no_more_updates = False
        heats = sorted(self.heats, key=lambda h: h.id)
        for n, heat in enumerate(heats):
            if no_more_updates:
                # only update upcoming heats if they're currently
                # populated by placeholder athlete names
                athletes = [r.athlete.name for r in heat.athletes]
                if any(list(map(_is_placeholder_athlete_name, athletes))):
                    app.logger.info(f"Updating athletes for heat {heat.id}")
                    heat.update()
                continue
            else:
                app.logger.info(f"Updating heat {heat.id}")
                completed = heat.update()

                # if this heat is upcoming, then all proceeding
                # heats in this round are by definition upcoming
                # too, so we can stop trying to update heats
                if heat.status == 0:
                    no_more_updates = True

        # if the last heat returned completd = True,
        # then we're done
        self.completed = completed


class Event(mixins.Updatable, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    completed = db.Column(db.Boolean, default=False)
    year = db.Column(db.Integer, db.ForeignKey("season.year"))
    rounds = db.relationship("Round", backref="event", lazy="dynamic")

    @property
    def url(self):
        return parsers.get_event_url(self)

    @property
    def sorted_rounds(self):
        return sorted(self.rounds, key=lambda r: r.number)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)

        # first verify that status is ok and that we're close enough to the
        # event to warrant building it
        status, start_date = parsers.get_event_data_from_event_homepage(obj.url)
        if status in ("canceled", "postponed"):
            raise parsers.EventNotReady(
                "Status for event {} is currently {}".format(obj.name, status)
            )
        elif (
            datetime.datetime.now()
            + datetime.timedelta(days=Config.LEAD_DAYS_FOR_EVENT_CREATION)
        ) < start_date:
            raise parsers.EventNotReady(
                "Start date for event {} is {} days away, "
                "stopping creation".format(
                    obj.name, (start_date - datetime.datetime.now()).days
                )
            )

        # double check that event is ready to be scraped by
        # making sure that all the rounds have valid links
        try:
            round_ids = parsers.get_round_ids(obj.url + "/results")
        except parsers.EventNotReady:
            raise parsers.EventNotReady(
                "No valid round links for event {}".format(obj.name)
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
                    score = athlete.score or 0.0
                    csv_string += "\n{},{},{},{:0.2f}".format(
                        i, j, athlete.athlete.name, score
                    )
        return csv_string

    def _do_update(self):
        for round_ in self.rounds:
            # update returns completion status, so if
            # round hasn't completed after its own update,
            # stop because there's no sense updating rounds
            # that haven't begun yet
            if not round_.update():
                break
        else:
            # loop completed without breaking:
            # means all our rounds have completed
            self.completed = True


class Season(db.Model):
    year = db.Column(db.Integer, primary_key=True)
    events = db.relationship("Event", backref="season", lazy="dynamic")

    @property
    def url(self):
        return parsers.get_season_url(self)

    @classmethod
    def create(cls, year, **kwargs):
        # allow for possibility that season starts in late
        # of the year before
        if year > (datetime.datetime.now().year + 1):
            raise ValueError(
                "Cannot create season for future year {}".format(kwargs["year"])
            )

        # instantiate the season then add all the events we can to it
        obj = cls(year=year, **kwargs)
        for event_name, event_id in parsers.get_event_ids(obj.url).items():
            # skipping freshwater pro by default since
            # its format is so different
            if event_name == "freshwater-pro":
                continue

            # don't need to create events that have already been created
            # not quite sure why or when this might occur but hey why not
            event = Event.query.filter_by(
                name=event_name, id=event_id, season=obj
            ).first()
            if event is not None:
                continue

            # if event isn't ready, remove it from the session.
            # Otherwise add it
            try:
                event = Event.create(name=event_name, id=event_id, season=obj)
            except parsers.EventNotReady:
                bad_event = obj.query.filter_by(year=year).first()
                obj.events.remove(bad_event)
            else:
                db.session.add(event)
        return obj


class Athlete(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    heats = db.relationship("HeatResult", backref="result_athlete")


def delete_season(year):
    season = Season.query.filter_by(year=year)
    events = Event.query.filter_by(season=season.first())
    for event in events:
        rounds = Round.query.filter_by(event=event)
        for round in rounds:
            heats = Heat.query.filter_by(round=round)
            for heat in heats:
                HeatResult.query.filter_by(heat=heat).delete()
            heats.delete()
        rounds.delete()
    events.delete()
    season.delete()
