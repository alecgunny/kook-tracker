import time
import typing

from colorutils import Color
from flask import make_response, render_template, request

from app import Config, app, client, db, parsers
from app.kooks import kooks
from app.models import wsl

if typing.TYPE_CHECKING:
    from app.kooks import Kook


_SCORE_BREAKDOWN = [265, 1330, 3320, 4745, 6085, 7800, 10000]


@app.route("/")
def index():
    seasons = wsl.Season.query.all()
    seasons = [{"year": season.year} for season in seasons]
    return render_template("index.html", seasons=seasons)


@app.route("/seasons/<year>")
def season(year: int) -> str:
    """
    Returns an HTML page with a list of links
    to the given Season's Events
    """
    events = wsl.Event.query.filter_by(year=year)
    events = [{"name": event.name} for event in events]
    for event in events:
        event["title"] = event["name"].replace("-", " ").title()
    return render_template("season.html", event_year=year, events=events)


def _find_color_for_athlete(
    athlete_name: str, event: wsl.Event, kooks: typing.List["Kook"]
) -> str:
    """
    quick utility function for finding the color
    to assign to an athlete's box based on the
    kook that drafted them

    Paramters
    ---------
    :param athlete_name: Name of the athlete to which
        to assign a color for their Event page cells
    :parm event: The Event page for which this athlete's
        cells are being rendered
    :param kooks: List of kooks whose rosters to check
        for the given athlete

    Returns
    -------
    :return color: The color to associate with this
        athlete's cells on the event page
    """
    if wsl._is_placeholder_athlete_name(athlete_name):
        # for placeholders before an athlete
        # has been put into a slot, use a
        # generic grey color
        return "#bbbbbb"

    # otherwise look through all available kooks
    # to find the one that has the given athlete
    # on their roster for this event
    for kook in kooks:
        try:
            roster = kook.rosters[event.year][event.name]
        except KeyError:
            # this kook doesn't have a roster for
            # this event, move on
            continue

        if athlete_name in roster:
            # return the kook's color if the athlete
            # is on their roster
            return kook.color
    else:
        return None
        # we looped through all known kooks and
        # couldn't find one that has rostered
        # this athlete. Somethings' wrong.
        # raise ValueError(
        #     "Could not find kook with athlete {} on roster "
        #     "for event {} in season {}".format(
        #         athlete_name, event.name, event.year
        #     )
        # )


def _get_text_color(background_color: str) -> str:
    """
    Utility function for deciding whether to
    use black or white text depending on the
    background color of the given cell
    """
    # get the "value" of the color: i.e. a
    # number representing how light or dark
    # the color is
    _, __, v = Color(hex=background_color).hsv

    # if the value is sufficiently dark, use
    # white text, otherwise use black
    return "#ffffff" if v < 0.3 else "#000000"


def _build_athlete_rows(
    event: wsl.Event, kooks: typing.List["Kook"]
) -> typing.Tuple[typing.Dict, typing.List[float], typing.List[float]]:
    """
    top section of event page will be a large table displaying
    the heat-by-heat results from an event.
    attributes of cells in this table with be either `table`,
    if there's a table to display, or `title`, a special
    attribute reserved for the first row so that we know
    how many round columns to create
    """
    rounds = event.sorted_rounds
    first_row = []
    for n in range(len(rounds)):
        cell = {"table": False, "title": "Round {}".format(n + 1)}
        first_row.append(cell)
    rows = [first_row]

    last_round_complete, do_break = True, False
    for round in rounds:
        if not round.completed:
            # this round hasn't completed and so needs updating
            app.logger.info(
                f"Updating round {round.id} for event {event.name}"
            )
            this_round_complete = round.update()
            if do_break:
                break

            if last_round_complete and not this_round_complete:
                # the previous round is complete but this one
                # isn't. This means we need to do one more
                # update on the _next_ round to fill in any
                # athletes that have won from this round
                # do this by setting a flag letting it
                # know to break after the next update
                do_break = True
                sleep_time = Config.CLIENT_WAIT_SECONDS - (
                    time.time() - client.last_call_time
                )
                if sleep_time > 0:
                    time.sleep(sleep_time)
            last_round_complete = this_round_complete

    # now piece together each row of the table separately
    heat_winning_scores, heat_losing_scores = {}, {}
    num_rows = max([len(round.heats.all()) for round in rounds])
    for i in range(num_rows):
        row = []
        for round in rounds:
            # try to get the heat for this row. If there aren't enough,
            # then we'll just leave it blank
            heats = round.sorted_heats
            try:
                heat = heats[i]
            except IndexError:
                row.append({"table": False, "title": False})
                continue

            # now build this table for this table *element*
            # record the winning score so that we can circle the
            # corresponding box
            table = []
            max_score = max([result.score or 0 for result in heat.athletes])
            min_score = min([result.score or 0 for result in heat.athletes])
            heat_winning_scores[heat.id] = max_score
            heat_losing_scores[heat.id] = min_score
            for result in heat.athletes:
                name = result.athlete.name

                # find the background color this athlete's cell
                # should have based on the kook that drafted them
                # add an alpha value based on the status of the heat
                background = _find_color_for_athlete(name, event, kooks)

                winner = heat.completed
                if round.number < 2:
                    winner &= result.score != min_score
                else:
                    winner &= result.score == max_score

                if background is None:
                    background = "#888888"
                    border_color = "#ff0000"
                    border_width = 3
                elif winner:
                    border_color = "#000000"
                    border_width = 5
                else:
                    border_color = "#ffffff"
                    border_width = 1

                background += ["55", "bb", "ff"][heat.status]
                border = f"{border_width}px solid {border_color}"
                table.append(
                    {
                        "name": name,
                        "background": background,
                        "score": result.score,
                        "text": _get_text_color(background),
                        "border": border,
                    }
                )
            row.append({"table": table, "title": False})
        rows.append(row)
    return rows, heat_winning_scores, heat_losing_scores


def _compute_points_possible(athletes: typing.List[typing.Dict]) -> float:
    """
    Given a roster of athletes and some associated
    metadata, return the number of possible points
    such a roster can score for a given event.

    Parameters
    ----------
    :param athletes: A list of dictionaries with the
        following keys for specifying athletes on a roster:
        - `name`: The athlete name
        - `score`: The total points the athlete has scored
            for their kook thus far in the event
        - `heat`: Which heat number in an elimination round
            the athlete last occupied, or `None` if they
            haven't reached an elimination round
        - `completed`: Whether the athlete has finished
            competing in this event or not

    Returns
    -------
    :return points_possible: How many points the kook
        with this roster can still score in the given
        event
    """

    num_rounds = len(_SCORE_BREAKDOWN) - 1

    # make a list of the points that can be achieved
    # by finishing in a given position in the Event
    positions = []
    for n, i in enumerate(_SCORE_BREAKDOWN):
        exponent = max(num_rounds - n - 1, 0)
        positions.append([i] * 2 ** exponent)

    # initialize the points possible counter, as
    # well as how many athletes on the given roster
    # whose elimination heat position is as yet unknown
    points_possible, leftover_positions = 0, 0
    heat_idx = []
    for athlete in athletes:
        heat = athlete.pop("heat")
        completed = athlete.pop("completed")
        if heat == "N/A":
            continue

        if completed:
            # the athlete has stopped competing, so add
            # their scored points to the total
            points_possible += athlete["score"]
        elif heat is None:
            # this athlete has not been given an elimination
            # heat yet, so defer making judgements about
            # how many points they can score until later
            leftover_positions += 1
        else:
            # otherwise record which heat this athlete
            # is in to track which athletes might
            # be forced to compete with one another
            # before the finals
            heat_idx.append(heat)

    # simulate the Event heats for all elimination
    # rounds to see when two rostered athletes might
    # need to compete against one another
    round_idx = 1
    while len(heat_idx) > 1:
        # calculate how many heats the rostered athletes
        # will be competing in in this round
        unique_heats = set(heat_idx)
        for _ in range(len(heat_idx) - len(unique_heats)):
            # if it is less than the total number of athletes,
            # at least two of the rostered athletes are
            # competing against one another, therfore
            # take the corresponding score from this round
            # for each athlete this must stop here
            points_possible += positions[round_idx].pop(0)

        # increment all the heat indices forwared to
        # the next round by dividing them by two
        # and then increment the round
        heat_idx = [i // 2 for i in unique_heats]
        round_idx += 1

    if len(heat_idx) == 1:
        # if we've gotten all the way to the end
        # and we still have one athlete, add the
        # winning score to the total
        points_possible += positions[-1].pop(0)

    # for those athletes which have not been seeded
    # in an elimination round yet, take the most
    # optimistic assumption and grant them all the
    # highest possible remaining point totals
    for _ in range(leftover_positions):
        for round in positions[::-1]:
            # iterate through the rounds backwards, starting
            # with the most valuable
            if round:
                # if there are any spots left to finish in
                # this round, add the corresponding amount
                # of points to the running total
                points_possible += round.pop(0)
                break

    # return the total possible number of points
    # this roster can still score
    return points_possible


def _build_kook_rows(event, kooks, heat_winning_scores, heat_losing_scores):
    kook_rows = []
    idx, row = 0, []
    rounds = [r.sorted_heats for r in event.sorted_rounds]

    for kook in kooks:
        kook_dict = {
            "background": kook.color,
            "text": _get_text_color(kook.color),
            "name": kook.name,
        }

        total_score, athletes = 0, []
        try:
            roster = kook.rosters[event.year][event.name]
        except KeyError:
            continue

        for athlete_name in roster:
            athlete = wsl.Athlete.query.filter_by(name=athlete_name).first()
            if athlete is None:
                app.logger.warning(f"No athlete '{athlete_name}' in database")
                athletes.append(
                    {
                        "name": athlete_name,
                        "score": "N/A",
                        "heat": "N/A",
                        "completed": True,
                    }
                )
                continue

            elimination_heat = None

            for i, round in enumerate(rounds):
                for j, heat in enumerate(round):
                    heat_result = wsl.HeatResult.query.filter_by(
                        athlete_id=athlete.id, heat_id=heat.id
                    ).first()

                    if heat_result is not None:
                        break
                else:
                    if i != 1:
                        last_heat = heat
                        break
                    else:
                        continue

                winner = heat.completed
                if i < 2:
                    winner &= heat_result.score != heat_losing_scores[heat.id]
                else:
                    winner &= heat_result.score == heat_winning_scores[heat.id]

                last_heat = heat
                if i == 2:
                    elimination_heat = j
            else:
                i += 2 if winner else 1

            score = _SCORE_BREAKDOWN[max(i - 2, 0)]
            total_score += score
            athletes.append(
                {
                    "name": athlete_name,
                    "score": score,
                    "heat": elimination_heat,
                    "completed": last_heat.completed and not winner,
                }
            )

        kook_dict["score"] = total_score
        kook_dict["athletes"] = athletes
        kook_dict["possible"] = _compute_points_possible(athletes)

        # reset row after every 3. TODO: something more robust here
        # for configurable competitor sizes and displays
        row.append(kook_dict)
        idx += 1
        if idx == 3:
            kook_rows.append(row)
            idx, row = 0, []
    return kook_rows


@app.route("/seasons/<year>/event/<name>")
def event(year, name):
    app.logger.debug(f"Getting data for {year} event {name}")
    event_name = name
    event = wsl.Event.query.filter_by(year=year, name=event_name).first()
    app.logger.debug(f"Found {year} event {name} in database")

    rows, heat_winning_scores, heat_losing_scores = _build_athlete_rows(
        event, kooks
    )
    app.logger.debug(f"Retrieved {len(rows)} of athlete data")

    kook_rows = _build_kook_rows(
        event, kooks, heat_winning_scores, heat_losing_scores
    )
    app.logger.debug(f"Retrieved {len(kook_rows)} of kook data")

    event_name = event_name.replace("-", " ").title()
    event_name = "{} {}".format(event_name, year)
    return render_template(
        "event.html", event_name=event_name, rows=rows, kook_rows=kook_rows
    )


def make_csv_response(csv_string):
    output = make_response(csv_string)
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route("/event-results")
def get_event_results():
    event_name = request.args.get("event-name")
    event_year = int(request.args.get("event-year"))

    # try to query event first to avoid having to query
    # season if we don't need to
    event = wsl.Event.query.filter_by(name=event_name, year=event_year).first()
    if event is None:
        # try to get the season in order to create the event
        season = wsl.Season.query.filter_by(year=event_year).first()

        # if it doesn't exist, then create it and try to get the
        # event again
        # TODO: this won't work for a real request, which won't
        # want to sit there while the event, let alone the season,
        # gets created
        if season is None:
            season = wsl.Season.create(year=event_year)
            db.session.add(season)
            db.session.commit()
            event = wsl.Event.query.filter_by(
                name=event_name, year=event_year
            ).first()

            # event will have just been created and so will have the
            # most up-to-date results
            if event is not None:
                return make_csv_response(event.results)

    # Try to create the event if season creation wasn't enough
    # to make it not None. At the very least we'll get a more
    # informative error as to what's invalid about it
    if event is None:
        event_id = parsers.get_event_ids(season.url, event_names=event_name)[
            event_name
        ]
        event = wsl.Event.create(name=event_name, id=event_id, season=season)
        db.session.add(event)

    # update the event if we didn't need to create it
    elif not event.completed:
        event.update()

    # commit updates and return response
    db.session.commit()
    return make_csv_response(event.results)


@app.route("/reset")
def reset_event():
    year = request.args.get("year")
    name = request.args.get("name")
    event = wsl.Event.query.filter_by(year=year, name=name).first()
    if event is None:
        return "No event", 400

    id = event.id
    season = event.season

    objects_deleted = 0
    rounds = wsl.Round.query.filter_by(event=event)
    for round in rounds:
        heats = wsl.Heat.query.filter_by(round=round)
        for heat in heats:
            objects_deleted += wsl.HeatResult.query.filter_by(
                heat=heat
            ).delete()
        objects_deleted += heats.delete()
    objects_deleted += rounds.delete()

    db.session.delete(event)
    db.session.commit()
    app.logger.info("Deleted {} objects".format(objects_deleted + 1))

    app.logger.info("Creating new event {}".format(name))
    event = wsl.Event.create(name=name, season=season, id=id)
    app.logger.info("Event created")

    db.session.add(event)
    db.session.commit()
    app.logger.info("Event added to database")

    return "Success!", 200
