from flask import request, make_response, render_template
from app import app, db, parsers
from app.models import wsl

from colorutils import Color


@app.route('/')
def index():
  seasons = wsl.Season.query.all()
  seasons = [{'year': season.year} for season in seasons]
  return render_template('index.html', seasons=seasons)


@app.route('/seasons/<year>')
def season(year):
  events = wsl.Event.query.filter_by(year=year)
  events = [{'name': event.name} for event in events]
  for event in events:
    event['title'] = event['name'].replace('-', ' ').title()
  return render_template('season.html', event_year=year, events=events)


@app.route('/seasons/<year>/event/<name>')
def event(year, name):
  from app.kooks import kooks
  event = wsl.Event.query.filter_by(year=year, name=name).first()
  def find_color_for_athlete(athlete_name):
    for kook, attrs in kooks.items():
      if athlete_name in attrs["athletes"]:
        return attrs["color"]
    else:
      print("Could not find kook with athlete {}".format(athlete_name))

  default_cell = {
    "name": "TBD",
    "background": "#ffffff",
    "score": 0.0
  }
  row = [{
      "table": False,
      "title": "Round {}".format(n+1)
    } for n, round in enumerate(event.rounds)]
  rows = [row]
  num_rows = max([len(list(round.heats)) for round in event.rounds])
  for i in range(num_rows):
    row = []
    for round in event.rounds:
      try:
        heat = round.heats[i]
      except IndexError:
        row.append({"table": False, "title": False})
        continue

      table = []
      max_score = max([result.score for result in heat.athletes])
      for result in heat.athletes:
        name = result.athlete.name
        background = find_color_for_athlete(name)

        h, s, v = Color(hex=background).hsv
        text_color = "#ffffff" if v < 0.3 else "#000000"

        winner = result.score == max_score
        border = "5px solid #000000" if winner else "1px solid #ffffff"
        table.append({
          "name": name,
          "background": background,
          "score": result.score,
          "text": text_color,
          "border": border
        })
      row.append({"table": table, "title": False})
    rows.append(row)

  _SCORE_BREAKDOWN = [265, 1330, 3320, 4745, 6085, 7800, 10000]
  kook_rows = []
  idx, row = 0, []
  for kook, attrs in kooks.items():
    h, s, v = Color(hex=attrs["color"]).hsv
    text_color = "#ffffff" if v < 0.3 else "#000000"
    kook_dict = {"background": attrs["color"], "text": text_color, "name": kook}
    total_score, athletes = 0, []
    for athlete_name in attrs["athletes"]:
      athlete = wsl.Athlete.query.filter_by(name=athlete_name).first()
      for n, round in enumerate(event.rounds[2:]):
        for heat in round.heats:
          heat_result = wsl.HeatResult.query.filter_by(
            athlete_id=athlete.id, heat_id=heat.id).first()
          if heat_result is not None:
            if n == (len(list(event.rounds)) - 3):
              n += 1
              winning_score = max([result.score for result in heat.athletes])
              if heat_result.score == winning_score:
                n += 1
            break
        else:
          break
      score = _SCORE_BREAKDOWN[n]
      total_score += score
      athletes.append({"name": athlete_name, "score": score})

    kook_dict["score"] = total_score
    kook_dict["athletes"] = athletes

    row.append(kook_dict)
    idx += 1
    if idx == 3:
      kook_rows.append(row)
      idx, row = 0, []
  return render_template('event.html', rows=rows, kook_rows=kook_rows)


def make_csv_response(csv_string):
  output = make_response(csv_string)
  output.headers["Content-Disposition"] = "attachment; filename=export.csv"
  output.headers["Content-type"] = "text/csv"
  return output


@app.route('/event-results')
def get_event_results():
  event_name = request.args.get('event-name')
  event_year = int(request.args.get('event-year'))

  # try to query event first to avoid having to query
  # season if we don't need to
  event = wsl.Event.query.filter_by(
    name=event_name, year=event_year).first()
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
        name=event_name, year=event_year).first()

      # event will have just been created and so will have the
      # most up-to-date results
      if event is not None:
        return make_csv_response(event.results)

  # Try to create the event if season creation wasn't enough
  # to make it not None. At the very least we'll get a more
  # informative error as to what's invalid about it
  if event is None:
    event_id = parsers.get_event_ids(season.url, event_names=event_name)
    event = wsl.Event.create(name=event_name, id=event_id, season=season)
    db.session.add(event)

  # update the event if we didn't need to create it
  elif not event.completed:
    event.update()

  # commit updates and return response
  db.session.commit()
  return make_csv_response(event.results)
