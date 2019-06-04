import urllib
from bs4 import BeautifulSoup as bs
import json
import time
import datetime
from collections import OrderedDict


_HOMEPAGE_URL = "https://www.worldsurfleague.com"
_SECS_BETWEEN_CALLS = 2
_SCORE_BREAKDOWN = [265, 265, 1330, 3320, 4745, 6085, 7800, 10000]


class Client:
  def __init__(self, wait_time=_SECS_BETWEEN_CALLS):
    self.wait_time = wait_time
    self.last_call_time = time.time()

  @property
  def sleeping(self):
    return time.time() - self.last_call_time < self.wait_time

  def __call__(self, url):
    while self.sleeping:
      time.sleep(0.01)

    with urllib.request.urlopen(url) as html:
      self.last_call_time = time.time()
      return bs(html, 'lxml')


client = Client()


def get_athlete_rankings(year):
  athletes_url = "{}/athletes/tour/mct?year={}".format(
      _HOMEPAGE_URL, year)
  athlete_soup = client(athletes_url)
  names = athlete_soup.find_all('a', class_='athlete-name')
  return [name.text for name in names]


class Heat:
  def __init__(self, url, heat_div):
    self.url = url
    self.id = heat_div.attrs['data-heat-id']
    self._update_status(heat_div)

  def _update_status(self, div):
    heat_status_span = div.find('span', class_='hot-heat__status')
    self.status = heat_status_span.attrs['class'][1].split('--')[1]

    self._completed = self.status == 'over'
    self._score_map = self._get_scores_and_athlete_names(div)
    self._div = div

  def _get_scores_and_athlete_names(self, div):
    score_map = OrderedDict()
    athlete_divs = div.find_all(
      'div', class_='hot-heat-athlete__name--full')
    for div in athlete_divs:
      athlete_name = div.text
      score = div.find_next_sibling(
        'div', class_='hot-heat-athlete__score').text

      try:
        score_map[athlete_name] = float(score)
      except ValueError:
        score_map[athlete_name] = None if self.status == 'upcoming' else 0

    return score_map

  def _maybe_update(func):
    def check_then_run(self):
      if not self._completed and not client.sleeping:
        soup = client(self.url)
        div = soup.find(
          'div', class_='post-event-watch-heat-grid__heat', attrs={
            'data-heat-id': self.id})
        self._update_status(div)
      return func(self)
    return check_then_run

  @property
  @_maybe_update
  def div(self):
    return self._div

  @property
  @_maybe_update
  def completed(self):
    return self._completed

  @property
  @_maybe_update
  def score_map(self):
    return self._score_map

  @property
  def scores(self):
    return [i for i in self.score_map.values()]

  @property
  def athlete_names(self):
    # using _score_map because this should be static, right?
    return [i for i in self._score_map.keys()]

  def first_or_last(self, first):
    if self.completed:
      return sorted(
        self.score_map.keys(),
        key=lambda key: self.score_map[key] or -99,
        reverse=first)[0]
    return None

  @property
  def winner(self):
    return self.first_or_last(first=True)

  @property
  def loser(self):
    return self.first_or_last(first=False)


class Round(object):
  def __init__(self, url):
    self.url = url
    self.initialized = False

    soup = client(self.url)
    self.heats = []
    heat_divs = soup.find_all(
      'div', class_='post-event-watch-heat-grid__heat')
    for div in heat_divs:
      self.heats.append(Heat(self.url, div))

  @property
  def completed(self):
    return all([heat.completed for heat in self.heats])

  @property
  def num_heats(self):
    return len(self.heats)

  @property
  def athlete_names(self):
    return [
      athlete for heat in self.heats for athlete in heat.athlete_names]

  @property
  def winners(self):
    return [heat.winner for heat in self.heats]

  @property
  def losers(self):
    return [heat.loser for heat in self.heats]


class Event:
  def __init__(self, name, year, event_id, draft_date):
    self.name = name
    self.year = year

    self.base_url = '{}/events/{}/mct/{}/{}/results'.format(
      _HOMEPAGE_URL, year, event_id, name)
    results_soup = client(self.base_url)

    # use the links to the individual rounds to get the round ids
    round_link_divs = results_soup.find_all(
      'div', class_='post-event-watch-round-nav__item')
    self.round_ids = []
    for div in round_link_divs:
      self.round_ids.append(
        json.loads(div.find('a').attrs['data-gtm-event'])['round-ids'])

    initial_round = Round(self.get_round_url(0))
    self.all_athletes = initial_round.athlete_names

    self.rounds = [initial_round]
    self._completed = False
    self._winning_athlete = None
    self._update_rounds()

    self.competitors = []
    self.draft_order = []
    self.has_drafted = False
    self.draft_date = draft_date

    self.default_athlete_draft_order = get_athlete_rankings(year)
    self.default_athlete_draft_order = [
      i for i in self.default_athlete_draft_order if i in self.all_athletes]

  def get_round_url(self, round_number):
    return "{}?roundId={}".format(self.base_url, self.round_ids[round_number])

  def _update_rounds(self):
    while True:
      if self._completed:
        break
      elif (
          self.current_round.completed and
          len(self.rounds) < len(self.round_ids)):
        next_round = Round(self.get_round_url(len(self.rounds)))
        self.rounds.append(next_round)
        self._update_results()
      else:
        self._update_results()
        break 

  def _update_results(self):
    results = OrderedDict()
    for athlete in self.all_athletes:
      for n, round_ in enumerate(self.rounds):
        if athlete not in round_.athlete_names:
          if n == 1:
            continue
          break

        # check if heat has completed and athlete has won
        if athlete in round_.losers:
          results[athlete] = max(n, 1)
        elif athlete in round_.winners:
          results[athlete] = max(n+1, 2)
        else:
          # if the heat has completed, then this means the athlete was the
          # middle athlete in the seeding or elimination round. Otherwise
          # the heat hasn't completed yet
          athlete_heat = [
            heat for heat in round_.heats if athlete in heat.athlete_names][0]
          results[athlete] = 2 if athlete_heat.completed else n

      # check if athlete is event champion
      if (round_.completed and
          round_.num_heats == 1 and
          round_.heats[0].winner == athlete):
        self._completed = True
        results[athlete] = 7
        self.winning_athlete = athlete

    self._athlete_results = results

  def _maybe_update(func):
    def check_then_run(self):
      if not self._completed:
        self._update_rounds()
      return func(self)
    return check_then_run

  @property
  def current_round(self):
    return self.rounds[-1]

  @property
  @_maybe_update
  def completed(self):
    return self._completed

  @property
  @_maybe_update
  def athlete_results(self):
    return self._athlete_results

  @property
  def athlete_scores(self):
    return {
      athlete: _SCORE_BREAKDOWN[n] for athlete, n in
        self.athlete_results.items()}

  @property
  @_maybe_update
  def athlete_results_csv(self):
    csv_string = "RoundNum,HeatNum,AthleteName,Score"
    for i, round_ in enumerate(self.rounds):
      for j, heat in enumerate(round_.heats):
        for athlete, score in heat.score_map.items():
          csv_string += "\n{},{},{},{}".format(
            i, j, athlete, score)
    return csv_string

  def add_competitor(self, competitor):
    if not competitor in self.competitors:
      self.competitors.append(competitor)
      self.draft_order.append(competitor)
      competitor.add_event(self)

  def add_competitors(self, competitors):
    for competitor in competitors:
      self.add_competitor(competitor)

  def update_draft_order(self, competitor, new_position):
    assert new_position in range(len(self.all_athletes))
    assert competitor in self.competitors

    self.draft_order.remove(competitor)
    self.draft_order.insert(new_position, competitor)

  def draft(self):
    if len(self.competitors) == 0:
      print("Nothing to draft!")
      return

    remaining_surfers = self.all_athletes.copy()
    while len(remaining_surfers) > 0:
      for competitor in self.draft_order:
        drafted_surfer = competitor.draft(self, remaining_surfers)
        remaining_surfers.remove(drafted_surfer)
    self.has_drafted = True

  @property
  def competitor_scores(self):
    athlete_scores = self.athlete_scores
    get_score = lambda competitor : \
      sum([athlete_scores[athlete] for athlete in
             competitor.events[self]['team']])
    return OrderedDict([
      (competitor, get_score(competitor)) for competitor in self.competitors])

  @property
  def ranked_competitors(self):
    competitor_scores = self.competitor_scores
    ranked_competitors = sorted(
      competitor_scores.keys(),
      key=lambda key: competitor_scores[key],
      reverse=True)
    return OrderedDict([
      (competitor, competitor_scores[competitor]) for
      competitor in ranked_competitors])

  @property
  def points_possible(self):
    points_possible = self.competitor_scores
    if self.completed:
      return points_possible

    remaining_available_points = []
    for i in range(8-len(self.rounds)):
      remaining_available_points.extend(
        [_SCORE_BREAKDOWN[-(i+1)]]*2**i)

    for competitor in self.competitors:
      team = competitor.events[self]['team']
      num_athletes_used = 0
      for n, athlete in enumerate(team):
        # if the athlete isn't currently competiting, skip them
        if athlete not in self.current_round.athlete_names:
          continue

        athlete_heat = [
          heat for heat in self.current_round.heats if
          athlete in heat.athlete_names][0]
 
        # if the athelete's heat has completed and they lost,
        # assuming this isn't the first round, skip them
        if (athlete_heat.completed and
            len(self.rounds) > 1 and
            athlete_heat.loser == athlete):
          continue

        # if athlete is still competing, but is competing against
        # another athlete on the competitor's team, skip the first
        # of these athletes
        on_competitors_team = (
          (set(team) - set([athlete])) & set(athlete_heat.athlete_names))
        if len(on_competitors_team) > 0:
          if list(on_competitors_team)[0] in team[n+1:]:
            continue

        # TODO: still doesn't take into account the possibility that two
        # athletes meet eachother at a later heat
        points_possible[competitor] += \
          remaining_available_points[num_athletes_used]
        num_athletes_used += 1
    return points_possible

  @property
  def winning_competitor(self):
    return self.ranked_competitors.keys()[0]


class Competitor:
  def __init__(self, name):
    self.name = name
    self.events = {}

  def add_event(self, event):
    if event not in self.events:
      self.events[event] = {
        'team': [],
        'draft_order': event.default_athlete_draft_order,
        'year_long_pick': event.default_athlete_draft_order[0]
      }

  def update_draft_order(self, event, surfer, new_position):
    assert event in self.events
    assert new_position in range(len(self.events[event]['draft_order']))
    assert surfer in self.events[event]['draft_order']

    self.events[event]['draft_order'].remove(surfer)
    self.events[event]['draft_order'].insert(new_position, surfer)

  def update_year_long_pick(self, event, surfer):
    assert surfer in event.all_athletes
    self.events[event]['year_long_pick'] = surfer

  def draft(self, event, remaining_surfers):
    for surfer in self.events[event]['draft_order']:
      if surfer in remaining_surfers:
        self.events[event]['team'].append(surfer)
        return surfer

  @property
  def event_scores(self):
    return {
      '{}-{}'.format(event.name, event.year): event.score(self) for
        event in self.events.keys()}


class League:
  def __init__(self, year):
    self.year = year
    self.base_url = '{}/events/{}/mct'.format(_HOMEPAGE_URL, year)
    self.update_events_info()
    self.events = []

  def update_events_info(self):
    soup = client(self.base_url)
    event_divs = soup.find_all('div', class_='tour-event-detail')
    events_info = {}
    for div in event_divs:
      try:
        event_url = div.find('a').attrs['href']
      except AttributeError:
        continue

      event_id, event_name = event_url.split("/")[-2:]
      events_info[event_name] = event_id
    self.events_info = events_info

  def create_event(self, event_name, draft_date=None):
    if event_name in [event.name for event in self.events]:
      return

    if draft_date is None:
      draft_date = datetime.datetime.fromtimestamp(time.time())

    event_id = self.events_info[event_name]
    self.events.append(Event(event_name, self.year, event_id, draft_date))

  def create_all_events(self):
    for event in self.events_info.keys():
      self.create_event(event)
 
  def get_event(self, event_name):
    return {event.name: event for event in self.events}[event_name]
