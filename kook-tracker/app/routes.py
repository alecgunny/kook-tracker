from flask import request, make_response
from app import app, db, parsers
from app.models import wsl


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
      event = wsl.Event.query.filter_by(
        name=event_name, year=event_year).first()

      # event will have just been created and so will have the
      # most up-to-date results
      if event is not None:
        db.session.commit()
        return make_csv_response(event.results)

  # Try to create the event if season creation wasn't enough
  # to make it not None. At the very least we'll get a more
  # informative error as to what's invalid about it
  if event is None:
    event_id = parsers.get_event_ids(season.url, event_names=event_name)
    event = Event.create(name=event_name, id=event_id, season=season)
    db.session.add(event)

  # update the event if we didn't need to create it
  elif not event.completed:
    event.update()
  db.session.commit()

  return make_csv_response(event.results)
