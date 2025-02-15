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

    heat = db.relationship("Heat", back_populates="athletes")
    athlete = db.relationship("Athlete", back_populates="heats")


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


class Athlete(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    heats = db.relationship("HeatResult", back_populates="athlete")


class Heat(mixins.Updatable, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    completed = db.Column(db.Boolean, default=False)
    status = db.Column(db.Integer, default=0)
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"))
    athletes = db.relationship("HeatResult", back_populates="heat")

    @classmethod
    def create(cls, **kwargs):
        obj = cls(completed=False, **kwargs)
        app.logger.info(f"Creating heat ID {obj.id}")
        obj.update()
        return obj

    def _do_update(self):
        try:
            status, scores = parsers.get_heat_data(self.round.url, self.id)
        except Exception as e:
            app.logger.error(e)
            return

        app.logger.debug(
            f"Read scores {scores} for heat {self.id} with status {status}"
        )
        self.update_with_status_and_scores(status, scores)

    def update_with_status_and_scores(self, status, scores):
        self.status = status

        for index, (athlete_name, score) in enumerate(scores):
            # if we're being reported a placeholder athlete name,
            # then make sure that the heat hasn't started yet. If it has,
            # we need to investigate
            if _is_placeholder_athlete_name(athlete_name) and status != 0:
                app.logger.warn(
                    f"Still using placeholder name {athlete_name} "
                    f"in ongoing heat {self.id}"
                )
                heat_result = HeatResult.query.filter_by(
                    heat=self, index=index
                )

                try:
                    athlete = heat_result.first().athlete
                except AttributeError:
                    # case 1: there's no existing entry, so just move on and
                    # pretend this never happend
                    continue

                # case 2: that heat result has a placeholder
                # name attached to it: delete it and move on
                if _is_placeholder_athlete_name(athlete.name):
                    app.logger.warn(
                        f"Removing placeholder heat result from heat {self.id}"
                    )
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
                app.logger.debug(f"Adding athlete {athlete_name} to database")
                db.session.add(athlete)
                db.session.commit()

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
                heat_result = HeatResult(
                    heat=self, index=index, athlete=athlete
                )
                self.athletes.append(heat_result)
            else:
                # second case: the heat has been created but the athlete
                # being used to instantiate is being updated
                if heat_result.athlete.name != athlete_name:
                    # if this is not because the instantiated athlete was
                    # a placeholder, we won't do this automatically, but
                    # will leave it to you to do manually if you think this
                    # is correct
                    if not _is_placeholder_athlete_name(
                        heat_result.athlete.name
                    ):
                        app.logger.warn(
                            "Athlete {} is being replaced by "
                            "athlete {} in heat {}.".format(
                                heat_result.athlete.name, athlete_name, self.id
                            )
                        )

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
        obj = cls(**kwargs)
        heat_ids = parsers.get_heat_ids(obj.url)
        for id in heat_ids:
            app.logger.debug(f"Creating heat {id}")
            Heat.create(id=id, round=obj)
        obj.completed = all([heat.completed for heat in obj.heats])
        return obj

    def _do_update(self):
        no_more_updates = False
        heats = sorted(self.heats, key=lambda h: h.id)
        for heat in heats:
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
    stat_id = db.Column(db.Integer)
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
    def create(cls, id: int, stat_id: int, name: str, year: int, **kwargs):
        obj = cls(id=id, stat_id=stat_id, name=name, year=year)

        # first verify that status is ok and that we're close enough to the
        # event to warrant building it
        status, start_date = parsers.get_event_data_from_event_homepage(obj)
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
            round_ids = parsers.get_round_ids(obj)
        except parsers.EventNotReady:
            raise parsers.EventNotReady(
                "No valid round links for event {}".format(obj.name)
            )

        # initialize all the internal rounds and heats
        kwargs = {"event": obj, "completed": False}
        for n, round_id in enumerate(round_ids):
            app.logger.debug(f"Creating round {round_id}")
            if n < 2:
                round_ = Round.create(id=round_id, number=n, **kwargs)
                continue
            else:
                round_ = Round(id=round_id, number=n, **kwargs)
                break

        rounds = parsers.parse_bracket(round_.url)
        for i in range(1, len(rounds) + 1):
            heats = rounds[round_.id]
            for id in sorted(heats.keys()):
                heat = Heat(id=id, completed=False, round=round_)
                status, scores = heats[id]
                heat.update_with_status_and_scores(status, scores)

            round_.completed = all([i.completed for i in round_.heats])

            if i < len(rounds):
                app.logger.debug(f"Creating round {round_id + i}")
                round_ = Round(id=round_id + i, number=2 + i, **kwargs)

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
        sorted_rounds = sorted(self.rounds, key=lambda round: round.id)

        # do first two rounds normally
        for round_ in sorted_rounds[:2]:
            if not round_.update():
                break
        else:
            # if both the first two rounds are completed,
            # start iterating through the bracket rounds
            rounds = parsers.parse_bracket(sorted_rounds[2].url)
            all_rounds_complete = True

            for round_ in sorted_rounds[2:]:
                if round_.completed:
                    continue

                all_heats_complete = True
                for heat in round_.sorted_heats:
                    if heat.completed:
                        continue

                    status, scores = rounds[round_.id][heat.id]
                    heat.update_with_status_and_scores(status, scores)

                    if not heat.status:
                        # if this heat is still upcoming, there's
                        # no point in updating anything after this
                        break
                    all_heats_complete &= heat.completed
                else:
                    # if we never broke, then all of the heats
                    # have at least started, so mark whether the
                    # round has completed and move on to the next
                    # one to account for potentially overlapping
                    # heats between rounds
                    round_.completed = all_heats_complete
                    all_rounds_complete &= all_heats_complete
                    continue

                # otherwise if we broke, one of this round's
                # heats hasn't started which means there's no
                # need to look at later rounds, so
                break
            else:
                # if all the rounds have completed, mark
                # the whole event as done
                self.completed = all_rounds_complete


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
            raise ValueError(f"Cannot create season for future year {year}")

        # instantiate the season then add all the events we can to it
        obj = cls(year=year, **kwargs)
        db.session.add(obj)
        for name, id in parsers.get_event_ids(obj.url).items():
            # skipping freshwater pro by default since
            # its format is so different
            if name == "freshwater-pro":
                continue

            # don't need to create events that have already been created
            # not quite sure why or when this might occur but hey why not
            event = Event.query.filter_by(name=name, id=id, season=obj).first()
            if event is not None:
                continue

            try:
                stat_id = parsers.get_event_stat_id(id, year, name)
            except ValueError:
                app.logger.info(
                    f"Skipping creation of event {name} {year} "
                    "because no stat ID was available"
                )
                continue

            # ignore this event if it's not ready yet
            try:
                event = Event.create(
                    name=name, id=id, stat_id=stat_id, year=year
                )
            except parsers.EventNotReady:
                continue
            else:
                obj.events.append(event)
                db.session.add(event)
                db.session.commit()
        return obj


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
