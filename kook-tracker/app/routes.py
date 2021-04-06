import time

from colorutils import Color
from flask import make_response, render_template, request

from app import Config, app, client, db, parsers
from app.models import wsl


@app.route("/")
def index():
    seasons = wsl.Season.query.all()
    seasons = [{"year": season.year} for season in seasons]
    return render_template("index.html", seasons=seasons)


@app.route("/seasons/<year>")
def season(year):
    events = wsl.Event.query.filter_by(year=year)
    events = [{"name": event.name} for event in events]
    for event in events:
        event["title"] = event["name"].replace("-", " ").title()
    return render_template("season.html", event_year=year, events=events)


def _find_color_for_athlete(athlete_name, event, kooks):
    """
    quick utility function for finding the color
    to assign to an athlete's box based on the
    kook that drafted them
    """
    if wsl._is_placeholder_athlete_name(athlete_name):
        return "#bbbbbb"

    for kook in kooks:
        try:
            roster = kook.rosters[event.year][event.name]
        except KeyError:
            continue
        if athlete_name in roster:
            return kook.color
    else:
        raise ValueError(
            "Could not find kook with athlete {} on roster "
            "for event {} in season {}".format(
                athlete_name, event.name, event.year
            )
        )


def _get_text_color(background_color):
    h, s, v = Color(hex=background_color).hsv
    return "#ffffff" if v < 0.3 else "#000000"


def _build_athlete_rows(event, kooks):
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
        if not round.completed and not client.sleeping:
            # this round hasn't completed and so needs updating
            app.logger.info(f"Updating round {round.id} for event {event.name}")
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
                time.sleep(sleep_time)
            last_round_complete = this_round_complete

    # now piece together each row of the table separately
    heat_winning_scores = {}
    num_rows = max([len(round.heats.all()) for round in rounds])
    for i in range(num_rows):
        row = []
        for round in rounds:
            # try to get the heat for this row. If there aren't enough,
            # then we'll just leave it blank
            try:
                heat = round.heats[i]
            except IndexError:
                row.append({"table": False, "title": False})
                continue

            # now build this table for this table *element*
            # record the winning score so that we can circle the
            # corresponding box
            table = []
            max_score = max([result.score or 0 for result in heat.athletes])
            heat_winning_scores[heat.id] = max_score
            for result in heat.athletes:
                name = result.athlete.name

                # find the background color this athlete's cell
                # should have based on the kook that drafted them
                # add an alpha value based on the status of the heat
                background = _find_color_for_athlete(name, event, kooks)
                background += ["55", "bb", "ff"][heat.status]

                winner = (result.score == max_score) and heat.completed
                border = "5px solid #000000" if winner else "1px solid #ffffff"
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
    return rows, heat_winning_scores


def _build_kook_rows(event, kooks, heat_winning_scores):
    _SCORE_BREAKDOWN = [265, 1330, 3320, 4745, 6085, 7800, 10000]
    kook_rows = []
    idx, row = 0, []
    rounds = event.sorted_rounds

    for kook in kooks:
        kook_dict = {
            "background": kook.color,
            "text": _get_text_color(kook.color),
            "name": kook.name,
        }

        total_score, athletes = 0, []
        for athlete_name in kook.rosters[event.year][event.name]:
            athlete = wsl.Athlete.query.filter_by(name=athlete_name).first()

            # only add a score to the base if the athlete
            # has progressed into the 3rd (1-based) round
            # or higher
            for n, round in enumerate(rounds[2:]):
                for heat in round.heats:
                    heat_result = wsl.HeatResult.query.filter_by(
                        athlete_id=athlete.id, heat_id=heat.id
                    ).first()

                    if heat_result is not None:
                        # there is a heat in this round featuring the athlete
                        if (n + 3) == len(list(rounds)):
                            # if we're in the last round, add an extra because
                            # we won't be able to iterate and increment again
                            n += 1

                            # check if they have the winning score and add
                            # another if they've won the whole comp
                            winning_score = heat_winning_scores[heat.id]
                            if heat_result.score == winning_score:
                                n += 1

                        # don't need to keep searching this round for the
                        # athlete, so exit
                        break
                else:
                    # the athlete is not in this round and has
                    # been eliminated, so stop iterating and
                    # assign the score
                    break

            score = _SCORE_BREAKDOWN[n]
            total_score += score
            athletes.append({"name": athlete_name, "score": score})

        kook_dict["score"] = total_score
        kook_dict["athletes"] = athletes

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
    # hard-code import of kook drafts while I don't have
    # a database set up for that info yet
    from app.kooks import kooks

    event_name = name
    event = wsl.Event.query.filter_by(year=year, name=event_name).first()

    rows, heat_winning_scores = _build_athlete_rows(event, kooks)
    kook_rows = _build_kook_rows(event, kooks, heat_winning_scores)

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
            objects_deleted += wsl.HeatResult.query.filter_by(heat=heat).delete()
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
