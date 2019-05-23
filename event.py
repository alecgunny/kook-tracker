import urllib
from bs4 import BeautifulSoup as bs
import json
import datetime
import time
from collections import OrderedDict


_HOMEPAGE_URL = "https://www.worldsurfleague.com"
_SECS_BETWEEN_CALLS = 2
_SCORE_BREAKDOWN = [265, 1330, 3320, 4745, 6085, 7800, 10000]


class Client(object):
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


class Heat(object):
  def __init__(self, round_, heat_div):
    self.round = round_
    self.id = heat_div.attrs['data-heat-id']
    self._update_status(heat_div)

  def _update_status(self, div):
    heat_status_span = div.find('span', class_='hot-heat__status')
    self.status = heat_status_span.attrs['class'][1].split("--")[1]

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
        score_map[athlete_name] = None

    return score_map

  def _check_for_update(func):
    def check_for_update(self):
      if not self._completed and not client.sleeping:
        soup = client(self.round.url)
        div = soup.find(
          'div', class_='post-event-watch-heat-grid__heat', attrs={
            'data-heat-id': self.id})
        self._update_status(div)
      return func(self)
    return check_for_update

  def _reduce_name(self, reduce_fn):
    if not self.completed:
      return None
    idx = self.scores.index(reduce_fn(self.scores))
    return self.athlete_names[idx]

  @property
  @_check_for_update
  def div(self):
    return self._div

  @property
  @_check_for_update
  def completed(self):
    return self._completed

  @property
  @_check_for_update
  def score_map(self):
    return self._score_map

  @property
  def scores(self):
    return [i for i in self.score_map.values()]

  @property
  def athlete_names(self):
    return [i for i in self.score_map.keys()]

  def first_or_last(self, first):
    if self.completed:
      return sorted(
        self.score_map.keys(),
        key=lambda x: self.score_map[key],
        reverse=first)[0]
    return None

  @property
  def winner(self):
    return first_or_last(first=True)

  @property
  def loser(self):
    return first_or_last(first=False)


class Round(object):
  def __init__(self, url):
    self.url = url
    self.initialized = False

    soup = client(self.url)
    self.heats = []
    heat_divs = soup.find_all(
      'div', class_='post-event-watch-heat-grid__heat')
    for div in heat_divs:
      self.heats.append(Heat(self, div))

  @property
  def completed(self):
    return all([heat.completed for heat in self.heats])

  @property
  def num_heats(self):
    return len(self.heats)

  @property
  def winners(self):
    return [heat.winner for heat in self.heats]

  @property
  def losers(self):
    return [heat.loser for heat in self.heats]


class Event(object):
  def __init__(self, name, year, event_id, draft_date):
    self.name = name
    self.year = year

    self.base_url = '{}/events/{}/mct/{}/{}/results'.format(
      _HOMEPAGE_URL, year, event_id, name)
    results_soup = client(self.base_url)
    first_round_link = results_soup.find(
      'div', class_='post-event-watch-round-nav__item').find('a')
    round_data = json.loads(first_round_link.attrs['data-gtm-event'])
    self.initial_round_id = int(round_data['round-ids'])
    self.rounds = [Round(self.get_round_url(0))]
    self.update_rounds()

    self.competitors = []
    self.competitor_draft_order = []
    self.has_drafted = False
    self.draft_date = draft_date

  def get_round_url(self, round_number):
    return "{}?roundId={}".format(
      self.base_url, str(self.initial_round_id+round_number))

  def update_rounds(self):
    while True:
      if self.current_round.completed and self.current_round.num_heats > 1:
        num_rounds_completed = len(self.rounds)
        next_round = Round(self.get_round_url(num_rounds_completed))
        self.rounds.append(next_round)
      else:
        break

  def monitor(self):
    while not self.completed:
      if not (self.has_drafted and 
          datetime.datetime.fromtimestamp(time.time()) >= self.draft_date):
        self.draft()
      self.update_rounds()

  @property
  def current_round(self):
    return self.rounds[-1]

  @property
  def completed(self):
    return (self.current_round.num_heats == 1 and self.current_round.completed)

  @property
  def winning_surfer(self):
    if self.completed:
      return self.current_round.heats[0].winner
    return None

  def add_competitor(self, competitor):
    if not competitor in self.competitors:
      self.competitors.append(competitor)
      self.competitor_draft_order.append(competitor)
      competitor.add_event(self)

  def update_draft_order(self, competitor, new_position):
    current_position = self.competitor_draft_order.index(competitor)
    del self.competitor_draft_order[current_position]
    self.competitor_draft_order.insert(new_position, competitor)

  def draft(self):
    remaining_surfers = self.default_athlete_draft_order.copy()
    while len(remaining_surfers) > 0:
      for competitor in self.competitor_draft_order:
        drafted_surfer = competitor.draft(self, remaining_surfers)
        del remaining_surfers[remaining_surfers.index(drafted_surfer)]
    self.has_drafted = True
  
  @property
  def default_athlete_draft_order(self):
    athletes_url = "{}/athletes/tour/mct?year={}".format(
      _HOMEPAGE_URL, self.year)
    athlete_soup = client(athletes_url)
    names = athlete_soup.find_all('a', class_='athlete-name')
    return [name.text for name in names][:36]

  def score(self, competitor):
    total_score = 0
    for surfer in competitor.events[self]['team']:
      surfer_score = _SCORE_BREAKDOWN[0]

      for n, round_ in enumerate(self.rounds[2:]):
        all_heat_athletes = [
          athlete for heat in round_.heats for athlete in heat.athlete_names]
        if surfer in all_heat_athletes:
          surfer_score = _SCORE_BREAKDOWN[n+1]
        else:
          break

      # check if event winner
      if self.winning_surfer == surfer:
        surfer_score = _SCORE_BREAKDOWN[-1]

      total_score += surfer_score
    return total_score

  @property
  def scores(self):
    return [self.score(competitor) for competitor in self.competitors]

  @property
  def ranked_scores(self):
    return sorted(self.scores, reverse=True)

  @property
  def ranked_competitors(self):
    return sorted(self.competitors, key=self.score, reverse=True)

  @property
  def winning_competitor(self):
    return self.ranked_competitors[0]


class Competitor(object):
  def __init__(self, name):
    self.name = name
    self.events = {}

  def add_event(self, event):
    if event not in self.events:
      self.events[event] = {
        'team': [], 'draft_order': event.default_athlete_draft_order}

  def update_draft_order(self, event, surfer, new_position):
    current_position = self.events[event]['draft_order'].index(surfer)
    del self.events[event]['draft_order'][current_position]
    self.events[event]['draft_order'][new_position] = surfer

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
