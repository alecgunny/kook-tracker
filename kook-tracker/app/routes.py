import typing
from collections import OrderedDict

from colorutils import Color
from flask import make_response, render_template, request

from app import app, db, parsers
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
    event_dicts, colors, totals = [], [], OrderedDict()
    for event in events:
        num_rounds = len([i for i in event.rounds])
        event_id = event.id
        event_name = event.name

        event = {"name": event_name}
        event["title"] = event_name.replace("-", " ").title()
        event["picks"] = []

        for kook in kooks:
            try:
                athlete_name = kook.year_longs[int(year)][event_name]
            except KeyError:
                app.logger.warning(
                    "No year long pick for kook {} in event {} {}".format(
                        kook.name, year, event_name
                    )
                )
                continue

            colors.append(
                {
                    "name": kook.name,
                    "color": kook.color,
                    "text": _get_text_color(kook.color),
                }
            )

            initials = _initialize(athlete_name)
            athlete = wsl.Athlete.query.filter_by(name=initials).first()
            score, _, __ = _compute_athlete_event_score(
                athlete, event_id, num_rounds
            )
            event["picks"].append((athlete_name, score))

            try:
                totals[kook.name] += score
            except KeyError:
                totals[kook.name] = score

        if len(event["picks"]) > 0:
            event_dicts.append(event)

    if len(totals) == 0:
        return render_template(
            "season.html", event_year=year, events=event_dicts
        )

    totals = list(totals.values())
    sort_totals = sorted(zip(totals, range(len(totals))), reverse=True)
    totals, idx = zip(*sort_totals)

    colors = [colors[i] for i in idx]
    for event in event_dicts:
        event["picks"] = [event["picks"][i] for i in idx]

    return render_template(
        "season-with-year-longs.html",
        event_year=year,
        events=event_dicts,
        kooks=colors,
        totals=totals,
    )


def _initialize(name):
    names = name.split()
    return names[0][0] + ". " + names[-1]


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

        roster = list(map(_initialize, roster))
        if athlete_name in roster:
            # return the kook's color if the athlete
            # is on their roster
            return kook.color
    else:
        # we looped through all the kooks and none of
        # them has rostered this athlete. Don't raise
        # an error, leave that to the calling process
        return None


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
            last_round_complete = this_round_complete

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
            scores = [result.score or 0 for result in heat.athletes]
            for result in heat.athletes:
                name = result.athlete.name

                # find the background color this athlete's cell
                # should have based on the kook that drafted them
                # add an alpha value based on the status of the heat
                background = _find_color_for_athlete(name, event, kooks)

                winner = heat.completed
                if round.number < 2 and len(rounds) > 6:
                    winner &= result.score != min(scores)
                else:
                    winner &= result.score == max(scores)

                if winner:
                    border_color = "#000000"
                    border_width = 5
                elif background is None:
                    border_color = "#000000"
                    border_width = 1
                else:
                    border_color = "#ffffff"
                    border_width = 1
                background = background or "#ffffff"

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
    return rows


def _compute_athlete_event_score(
    athlete: wsl.Athlete, event_id: int, num_rounds: int
) -> float:
    # elimination_heat = None
    offset = int(num_rounds == 6)
    results = (
        wsl.HeatResult.query.filter_by(athlete=athlete)
        .join(wsl.Heat, wsl.HeatResult.heat_id == wsl.Heat.id)
        .join(wsl.Round, wsl.Heat.round_id == wsl.Round.id)
        .join(wsl.Event, wsl.Round.event_id == wsl.Event.id)
        .filter_by(id=event_id)
    ).all()

    # find the result corresponding to this athletes
    # farthest round so far in the competition
    max_round_number, max_result = 0, None
    for result in results:
        if result.heat.round.number > max_round_number:
            max_result = result
            max_round_number = max_result.heat.round.number

    if max_result is None:
        return _SCORE_BREAKDOWN[offset], max_result, False

    # decide if the athlete "won" this heat
    # based on whether it has completed and
    # if they have the worst score or not
    if max_result.heat.completed:
        scores = [i.score or 0 for i in max_result.heat.athletes]
        scores = list(map(float, scores))
        score = float(max_result.score)
        winner = score != min(scores)
    else:
        winner = False

    # winners will always get an extra score index
    # from wherever their last round was
    max_round_number += 1 if winner else 0

    # if we only have six rounds, this is after the
    # cut and so the minimum score isn't given to anyone
    score_idx = max(max_round_number - 1, 0) + offset
    score = _SCORE_BREAKDOWN[score_idx]
    return score, max_result.heat, winner


def _compute_points_possible(
    heat_idx: typing.List[int],
    leftover_positions: int,
    score_breakdown: typing.List[int],
) -> float:
    """
    Given the indices of the heats occupied by a
    roster of athletes, as well as the number of
    athletes on a roster who haven't been seeded
    in an elimination heat yet, compute the highest
    possible score achievable by such a roster according
    to the given score breakdown.
    """

    num_rounds = len(score_breakdown) - 1

    # make a list of the points that can be achieved
    # by finishing in a given position in the Event
    positions = []
    for n, i in enumerate(score_breakdown):
        exponent = max(num_rounds - n - 1, 0)
        positions.append([i] * 2 ** exponent)

    # simulate the Event heats for all elimination
    # rounds to see when two rostered athletes might
    # need to compete against one another
    round_idx = 1
    points_possible = 0
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


def _build_kook_rows(event, kooks):
    kook_rows = []
    idx, row = 0, []
    rounds = [r.sorted_heats for r in event.sorted_rounds]
    num_rounds = len(rounds)

    for kook in kooks:
        # if this kook doesn't have a roster for this
        # competition, then we'll just move on
        try:
            roster = kook.rosters[event.year][event.name]
        except KeyError:
            continue

        # for each kook, construct a colored table with the
        # names of each athlete they have rostered, the
        # score that athlete has achieved so far in the
        # competition, as well as the total points the roster
        # has scored and _can possibly_ score in the competition
        kook_dict = {
            "background": kook.color,
            "text": _get_text_color(kook.color),
            "name": kook.name,
        }

        total_score, athletes = 0, []
        possible_score, leftover_spots, heat_idx = 0, 0, []
        for athlete_name in roster:
            athlete_name = _initialize(athlete_name)
            athlete = wsl.Athlete.query.filter_by(name=athlete_name).first()

            # if the athlete name is unrecoganized,
            # send back some blank data indicating this
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

            # compute the athlete's score so far, as well as the
            # last heat they competed in and whether they were
            # able to advance through it
            score, last_heat, winner = _compute_athlete_event_score(
                athlete, event.id, num_rounds
            )

            # add the score to the ongoing total score tally
            total_score += score

            # now do some gross logic to keep track of the points possible
            if (
                last_heat is not None
                and last_heat.round.number >= 1
                and last_heat.completed
                and not winner
            ):
                # this athlete is done, so add their current score
                # to the points possible tally and be done with it
                possible_score += score
            elif last_heat is not None and last_heat.round.number >= 2:
                # this athlete is still competing and will have been
                # assigned a heat in the elimination phase of the
                # tournament, so we can keep track of the indices of
                # these heats for this kook to figure out if any of
                # their athletes will compete before the finals
                heats = enumerate(last_heat.round.sorted_heats)
                hidx = [i for i, j in heats if j.id == last_heat.id][0]
                heat_idx.append(hidx)
            else:
                # this athlete has not been eliminated but has not
                # been assigned a heat in the elimination phase, so
                # we don't know where they'll end up. For points possible
                # then, we'll be optimistic and just assign this athlete
                # the best possible score once all the known spots are taken
                leftover_spots += 1

            athletes.append({"name": athlete_name, "score": score})

        # use the collected heat indices and number of
        # leftover spots to finish the points possible
        # calculation for this kook
        possible_score += _compute_points_possible(
            heat_idx, leftover_spots, _SCORE_BREAKDOWN[-num_rounds:]
        )

        kook_dict["score"] = total_score
        kook_dict["athletes"] = athletes
        kook_dict["possible"] = possible_score

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
    event = wsl.Event.query.filter_by(year=year, name=name).first()
    app.logger.debug(f"Found {year} event {name} in database")

    app.logger.debug(f"Updating event {name} {year}")
    completed = event.update()
    app.logger.debug(f"Event update returned status completed={completed}")

    rows = _build_athlete_rows(event, kooks)
    app.logger.debug(f"Retrieved {len(rows)} of athlete data")

    kook_rows = _build_kook_rows(event, kooks)
    app.logger.debug(f"Retrieved {len(kook_rows)} of kook data")

    name = name.replace("-", " ").title()
    name = "{} {}".format(name, year)
    return render_template(
        "event.html", event_name=name, rows=rows, kook_rows=kook_rows
    )


def make_csv_response(csv_string):
    output = make_response(csv_string)
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route("/event-results")
def get_event_results():
    name = request.args.get("name")
    year = int(request.args.get("year"))

    # try to query event first to avoid having to query
    # season if we don't need to
    event = wsl.Event.query.filter_by(name=name, year=year).first()
    if event is None:
        # try to get the season in order to create the event
        season = wsl.Season.query.filter_by(year=year).first()

        # if it doesn't exist, then create it
        # and try to get the event again
        if season is None:
            season = wsl.Season.create(year=year)
            event = wsl.Event.query.filter_by(name=name, year=year).first()

            # event will have just been created and so will have the
            # most up-to-date results
            if event is not None:
                return make_csv_response(event.results)

    # Try to create the event if season creation wasn't enough
    # to make it not None. At the very least we'll get a more
    # informative error as to what's invalid about it
    if event is None:
        id = parsers.get_event_ids(season.url, event_names=name)[name]
        stat_id = parsers.get_event_stat_id(id, year, name)
        event = wsl.Event.create(name=name, id=id, stat_id=stat_id, year=year)
        season.events.append(event)
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
    stat_id = event.stat_id

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
    event = wsl.Event.create(name=name, id=id, stat_id=stat_id, year=year)
    app.logger.info("Event created")

    db.session.add(event)
    db.session.commit()
    app.logger.info("Event added to database")

    return "Success!", 200
