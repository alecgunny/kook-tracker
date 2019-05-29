from flask import Flask, request, make_response
from league import League

app = Flask(__name__)

leagues = {}
for year in range(2019, 2020):
  league = League(year)
  league.create_all_events()
  leagues[year] = league


@app.route('/update')
def get_event_results():
  event_name = request.args.get('event-name')
  year = int(request.args.get('year'))

  league = leagues[year]
  if event_name not in league.events_info:
    league.update_events_info()
  assert event_name in league.events_info

  event = league.get_event(event_name)
  results_csv = event.athlete_results_csv
  output = make_response(results_csv)
  output.headers["Content-Disposition"] = "attachment; filename=export.csv"
  output.headers["Content-type"] = "text/csv"
  return output
