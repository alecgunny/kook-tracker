from flask import request, make_response
from app import app, db, updates
from app.models import wsl



@app.route('/event-results')
def get_event_results():
  event_name = request.args.get('event-name')
  event_year = request.args.get('event-year')

  season = wsl.Season.query.filter_by(year=event_year)
  if season is None:
    # insert code to try to create season
    raise ValueError('Unknown season year {}'.format(event_year))

  event = wsl.Event.query.filter_by(
    name=event_name, season_id=season.first().id
  )
  if event is None:
    # insert code to try to create event
    raise ValueError('Event name {} unrecognized'.format(event_name))
  event = event.first()

  if not event.completed:
    event.update()
  return event.results
