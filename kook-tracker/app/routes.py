import typing
from collections import OrderedDict
from itertools import groupby

from colorutils import Color
from flask import make_response, render_template, request

from app import app, db, parsers
from app.kooks import kooks, ranch_scores
from app.models import wsl

if typing.TYPE_CHECKING:
    from app.kooks import Kook


_SCORE_BREAKDOWN = [265, 1330, 3320, 4745, 6085, 7800, 10000]
# 2026+ format: bottom 8 seeds compete in an opening elimination round,
# then winners advance directly into a 32-person bracket stage.
_SCORE_BREAKDOWN_2026 = [500, 1000, 3320, 4745, 6085, 7800, 10000]
_ROUND_LABELS_2026 = [
    "Opening Round",
    "Round of 32",
    "Round of 16",
    "Quarterfinal",
    "Semifinal",
    "Final",
]


def _get_score_breakdown(year: int) -> typing.List[int]:
    if int(year) >= 2026:
        return _SCORE_BREAKDOWN_2026
    return _SCORE_BREAKDOWN


@app.route("/")
def index():
    seasons = wsl.Season.query.all()
    seasons = [{"year": season.year} for season in seasons]
    return render_template("index.html", seasons=seasons)


@app.route("/seasons/<year>")
def season(year: int) -> str:
    """
    Returns an HTML page summarizing the year-long picks for the
    given season: a matrix of each competitor's pick per event,
    season point totals, and gold/silver medals awarded to the
    competitors whose drafted *teams* placed 1st/2nd in each event.
    """
    events = wsl.Event.query.filter_by(year=year)
    event_dicts = []
    totals = OrderedDict()
    golds, silvers = {}, {}
    # competitor display info, keyed by name; insertion order preserved
    competitors = OrderedDict()

    for event in events:
        num_rounds = len([i for i in event.rounds])
        event_id = event.id
        event_name = event.name

        # award medals from the event-team standings: the competitor
        # whose drafted roster scored highest gets gold, second silver
        medal_for = _event_medals(event, kooks, num_rounds, year)

        # picks keyed by competitor name so we can emit them in a
        # consistent (sorted) column order later, regardless of which
        # competitors happen to have a pick for this event
        ev = {
            "name": event_name,
            "title": event_name.replace("-", " ").title(),
            "picks": {},
        }

        for kook in kooks:
            try:
                athlete_name = kook.year_longs[year][event_name]
            except KeyError:
                app.logger.warning(
                    "No year long pick for kook {} in event {} {}".format(
                        kook.name, year, event_name
                    )
                )
                continue

            competitors.setdefault(
                kook.name,
                {
                    "name": kook.name,
                    "color": kook.color,
                    "text": _get_text_color(kook.color),
                },
            )

            athlete = wsl.Athlete.query.filter_by(
                name=_initialize(athlete_name)
            ).first()
            score, _, __ = _compute_athlete_event_score(
                athlete, event_id, num_rounds, year
            )

            medal = medal_for.get(kook.name)
            ev["picks"][kook.name] = {
                "name": athlete_name,
                "score": score,
                "medal": medal,
            }
            if medal in ("gold", "gold-half"):
                golds[kook.name] = golds.get(kook.name, 0) + 1
            elif medal in ("silver", "silver-half"):
                silvers[kook.name] = silvers.get(kook.name, 0) + 1

            totals[kook.name] = totals.get(kook.name, 0) + score

        if ev["picks"]:
            event_dicts.append(ev)

    if len(totals) == 0:
        return render_template(
            "season.html", event_year=year, events=event_dicts
        )

    try:
        ranch = ranch_scores[int(year)]
    except KeyError:
        app.logger.warning(f"No ranch scores for year {year}")
    else:
        for kook in kooks:
            if kook.name not in totals:
                continue
            try:
                totals[kook.name] += ranch[kook.name]
            except KeyError:
                app.logger.warning(
                    "No ranch score for kook {} in year {}".format(
                        kook.name, year
                    )
                )

    # order competitors (columns) by season total, highest first
    competitors = list(competitors.values())
    competitors.sort(key=lambda c: totals[c["name"]], reverse=True)
    for comp in competitors:
        comp["gold"] = golds.get(comp["name"], 0)
        comp["silver"] = silvers.get(comp["name"], 0)

    total_list = [totals[c["name"]] for c in competitors]

    # flatten each event's picks into the same column order, filling a
    # blank for any competitor who lacks a pick for that event
    blank = {"name": "—", "score": 0, "medal": None}
    for ev in event_dicts:
        ev["picks"] = [ev["picks"].get(c["name"], blank) for c in competitors]

    return render_template(
        "season-with-year-longs.html",
        event_year=year,
        events=event_dicts,
        competitors=competitors,
        totals=total_list,
    )


def _initialize(name):
    names = name.split()
    return names[0][0] + ". " + names[-1]


def _initials(name: str) -> str:
    """Short team tag for a kook, e.g. 'Alec G' -> 'AG'."""
    return "".join(part[0] for part in name.split() if part).upper()


def _find_kook_for_athlete(
    athlete_name: str, event: wsl.Event, kooks: typing.List["Kook"]
) -> typing.Optional["Kook"]:
    """
    Find the kook (fantasy team) that drafted the given athlete
    for this event, or None if the slot is a placeholder or the
    athlete isn't on anyone's roster.

    Paramters
    ---------
    :param athlete_name: Name of the athlete whose drafting
        kook we're looking for
    :parm event: The Event page for which this athlete's
        cells are being rendered
    :param kooks: List of kooks whose rosters to check
        for the given athlete

    Returns
    -------
    :return kook: The Kook that rostered this athlete, or None
    """
    if wsl._is_placeholder_athlete_name(athlete_name):
        # placeholder before an athlete has been
        # put into a slot -- no owning kook
        return None

    # otherwise look through all available kooks
    # to find the one that has the given athlete
    # on their roster for this event
    for kook in kooks:
        try:
            roster = kook.rosters[str(event.year)][event.name]
        except KeyError:
            # this kook doesn't have a roster for
            # this event, move on
            continue

        roster = list(map(_initialize, roster))
        if athlete_name in roster:
            return kook

    # nobody has rostered this athlete
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
) -> typing.List[typing.Dict]:
    """
    Build the data for the heat-by-heat bracket section of the
    event page. Returns one entry per round, each with a title
    and a list of heats. Every heat carries its label, status,
    and the surfers competing in it -- annotated with the color
    and initials of the team that drafted them, and whether they
    advanced. Styling itself lives in event.css.
    """
    rounds = event.sorted_rounds

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

    is_2026 = int(event.year) >= 2026

    rounds_data = []
    for n, round in enumerate(rounds):
        if is_2026:
            title = _ROUND_LABELS_2026[n]
            # the opening round is a seeding/elimination round that
            # feeds into the bracket proper
            is_elimination = round.number == 0
        else:
            title = "Round {}".format(n + 1)
            # pre-2026 events with more than 6 rounds open with seeding
            # rounds (you advance by *not* finishing last)
            is_elimination = round.number < 2 and len(rounds) > 6

        heats_data = []
        for h, heat in enumerate(round.sorted_heats):
            scores = [result.score or 0 for result in heat.athletes]
            surfers = []
            for result in heat.athletes:
                name = result.athlete.name

                # find the team (and therefore color/initials) that
                # drafted this surfer for this event
                kook = _find_kook_for_athlete(name, event, kooks)

                # decide whether this surfer advanced out of the heat
                winner = heat.completed
                if round.number < 2 and len(rounds) > 6:
                    winner &= result.score != min(scores)
                else:
                    winner &= result.score == max(scores)

                surfers.append(
                    {
                        "name": name,
                        "score": result.score,
                        "color": kook.color if kook is not None else None,
                        "text": (
                            _get_text_color(kook.color) if kook else "#ffffff"
                        ),
                        "team": _initials(kook.name) if kook else "",
                        "winner": bool(winner),
                    }
                )

            heats_data.append(
                {
                    "label": "Heat {}".format(h + 1),
                    "status": heat.status,
                    "results": surfers,
                }
            )

        rounds_data.append(
            {
                "title": title,
                "heats": heats_data,
                "elimination": is_elimination,
            }
        )

    return rounds_data


def _compute_athlete_event_score(
    athlete: wsl.Athlete, event_id: int, num_rounds: int, year: int
) -> float:
    score_breakdown = _get_score_breakdown(year)
    # Pre-2026: 6-round events are post-cut (opening elim already occurred),
    # so offset by 1 to skip the lowest score tier.
    # 2026+: all 6 rounds are present (opening elim through final), no offset.
    if int(year) >= 2026:
        offset = 0
    else:
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
    max_round_number, max_result = -1, None
    for result in results:
        if result.heat.round.number > max_round_number:
            max_result = result
            max_round_number = max_result.heat.round.number

    if max_result is None:
        return score_breakdown[offset], max_result, False

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

    # 2026+: rounds are 0-indexed (0=Opening Round, 5=Final), so
    # max_round_number maps directly into score_breakdown after the
    # winner bonus above. Pre-2026: rounds are also 0-indexed but the
    # -1 adjustment + offset together shift into the correct tier.
    if int(year) >= 2026:
        score_idx = max_round_number
    else:
        score_idx = max(max_round_number - 1, 0) + offset
    score = score_breakdown[score_idx]
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
        positions.append([i] * 2**exponent)

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


def _event_team_scores(event, kooks, num_rounds, year):
    """
    Compute each competitor's total drafted-roster score for an event,
    used to rank teams and award medals on the season page. Returns a
    list of (kook_name, total_score) for kooks with a roster.
    """
    team_scores = []
    for kook in kooks:
        try:
            roster = kook.rosters[str(year)][event.name]
        except KeyError:
            continue

        total = 0
        for athlete_name in roster:
            athlete = wsl.Athlete.query.filter_by(
                name=_initialize(athlete_name)
            ).first()
            if athlete is None:
                continue
            score, _, __ = _compute_athlete_event_score(
                athlete, event.id, num_rounds, year
            )
            total += score
        team_scores.append((kook.name, total))
    return team_scores


def _event_medals(event, kooks, num_rounds, year):
    """
    Rank the event-team standings and award medals: the competitor
    whose drafted roster scored highest gets gold, second gets silver.

    Ties share a place: if N competitors tie for a medal position, they
    each get the "half" variant of that medal (e.g. two-way tie for first
    -> two "gold-half") and the shared place(s) are consumed, so a tie
    for first leaves no silver. Returns a dict mapping kook name to one
    of "gold", "silver", "gold-half", "silver-half".
    """
    team_scores = _event_team_scores(event, kooks, num_rounds, year)
    team_scores.sort(key=lambda kv: kv[1], reverse=True)

    medal_for = {}
    if not team_scores or team_scores[0][1] <= 0:
        # nothing scored yet -- no medals to award
        return medal_for

    # group competitors by identical score, highest first
    groups = [
        [name for name, _ in members]
        for _, members in groupby(team_scores, key=lambda kv: kv[1])
    ]

    first = groups[0]
    if len(first) > 1:
        # tie for first: split gold among them, no silver
        for name in first:
            medal_for[name] = "gold-half"
        return medal_for

    medal_for[first[0]] = "gold"
    if len(groups) >= 2:
        second = groups[1]
        suffix = "-half" if len(second) > 1 else ""
        for name in second:
            medal_for[name] = "silver" + suffix
    return medal_for


def _build_kook_rows(event, kooks):
    teams = []
    rounds = [r.sorted_heats for r in event.sorted_rounds]
    num_rounds = len(rounds)

    # 2026+: the full breakdown applies (opening round is included in the 6).
    # Pre-2026: 6-round events are post-cut, so slice off the lowest tier.
    _breakdown = _get_score_breakdown(event.year)
    if int(event.year) >= 2026:
        _breakdown_for_possible = _breakdown
    else:
        _breakdown_for_possible = _breakdown[-num_rounds:]

    for kook in kooks:
        # if this kook doesn't have a roster for this
        # competition, then we'll just move on
        try:
            roster = kook.rosters[str(event.year)][event.name]
        except KeyError:
            continue

        # for each kook, construct a colored table with the
        # names of each athlete they have rostered, the
        # score that athlete has achieved so far in the
        # competition, as well as the total points the roster
        # has scored and _can possibly_ score in the competition
        kook_dict = {
            "color": kook.color,
            "text": _get_text_color(kook.color),
            "initials": _initials(kook.name),
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
                athlete, event.id, num_rounds, event.year
            )

            # add the score to the ongoing total score tally
            total_score += score

            # now do some gross logic to keep track of the points possible
            min_done_round = 0 if int(event.year) >= 2026 else 1
            if (
                last_heat is not None
                and last_heat.round.number >= min_done_round
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
                print("YO!", athlete, last_heat.round.number, min_done_round)
                leftover_spots += 1

            athletes.append({"name": athlete_name, "score": score})

        # use the collected heat indices and number of
        # leftover spots to finish the points possible
        # calculation for this kook
        possible_score += _compute_points_possible(
            heat_idx, leftover_spots, _breakdown_for_possible
        )

        kook_dict["score"] = total_score
        kook_dict["athletes"] = athletes
        kook_dict["possible"] = possible_score

        teams.append(kook_dict)

    # present the standings as a leaderboard, highest score first
    teams.sort(key=lambda team: team["score"], reverse=True)
    return teams


@app.route("/seasons/<year>/event/<name>")
def event(year, name):
    app.logger.debug(f"Getting data for {year} event {name}")
    event = wsl.Event.query.filter_by(year=year, name=name).first()
    app.logger.debug(f"Found {year} event {name} in database")

    app.logger.debug(f"Updating event {name} {year}")
    completed = event.update()
    app.logger.debug(f"Event update returned status completed={completed}")

    rounds = _build_athlete_rows(event, kooks)
    app.logger.debug(f"Retrieved {len(rounds)} rounds of athlete data")

    teams = _build_kook_rows(event, kooks)
    app.logger.debug(f"Retrieved {len(teams)} teams of kook data")

    name = name.replace("-", " ").title()
    name = "{} {}".format(name, year)
    return render_template(
        "event.html",
        event_name=name,
        event_year=year,
        rounds=rounds,
        teams=teams,
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
