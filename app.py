from flask import Flask, request, make_response

app = Flask(__name__)

league = League(2019)
league.add_event('rip-curl-pro-bells-beach')

leagues = {2019: league}

@app.route('/update')
def get_event_info():
  event_name = request.args.get('event-name')
  year = int(request.args.get('year'))

  event = leagues[year].get_event(event_name)
  results_csv = event.athlete_results_csv
  output = make_response(results_csv)
  output.headers["Content-Disposition"] = "attachment; filename=export.csv"
  output.headers["Content-type"] = "text/csv"
  return output
