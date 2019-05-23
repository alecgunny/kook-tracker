import urllib
from bs4 import BeautifulSoup as bs
import itertools
import json
import datetime
import time


_HOMEPAGE_URL = "www.worldsurfleague.com"


def load_soup(url):
  with urllib.request.urlopen(url) as html:
    return bs(html, 'lxml')


class Heat(object):
  def __init__(self, athlete_names, scores):
    self.athlete_names = athlete_names
    self.scores = scores

  def add_score(self, athlete_name, score):
    assert athlete_name in self.athlete_names
    self.scores[self.athlete_names.index(athlete_name)] = score

  def _reduce_name(self, reduce_fn):
    if not self.completed:
      return None
    idx = self.scores.index(reduce_fn(self.scores))
    return self.athlete_names[idx]

  @property
  def completed(self):
    return all([score is not None for score in self.scores])

  @property
  def winner(self):
    return self._reduce_name(max)

  @property
  def loser(self):
    return self._reduce_name(min)


class Round(object):
  def __init__(self, url):
    self.url = url
    self.initialized = False
    self.update_heats()

  def update_heats(self):
    soup = load_soup(self.url)
    if not self.initialized:
      self.heats = itertools.cycle([None])

    heat_divs = soup.find_all(
      'div', class_='post-event-watch-heat-grid__heat')
    initial_heats = []
    for heat, div in zip(self.heats, heat_divs):
      if heat is not None and heat.completed:
        continue
  
      athletes, scores = [], []
      athlete_divs = div.find_all(
        'div', class_='hot-heat-athlete__name--full')
      for a_div in athlete_divs:
        athletes.append(a_div.text)
        score = a_div.find_next_sibling(
          'div', class_='hot-heat-athlete__score').text

        try:
          scores.append(float(score))
        except ValueError:
          scores.append(None)

      if heat is not None:
        for athlete, score in zip(athletes, scores):
          heat.add_score(athlete, score)
      else:
        initial_heats.append(Heat(athletes, scores))

    if not self.initialized:
      self.heats = initial_heats
      self.initialized = True

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

    self.base_url = "{}/events/{}/mct/{}/{}/results'.format(
      _HOMEPAGE_URL, year, event_id, name)
    results_soup = load_soup(self.base_url)
    first_round_link = results_soup.find(
      'div', class_='post-event-watch-round-nav__item').find('a')
    round_data = json.loads(first_round_link.attrs['data-gtm-event'])
    self.initial_round_id = int(round_data['round-ids'])
    self.rounds = [Round(self.get_round_url(0))]
    self.update_rounds()

    self.competitors = []
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
      self.current_round.update_heats()

  @property
  def current_round(self):
    return self.rounds[-1]

  @property
  def completed(self):
    return (self.current_round.num_heats == 1 and self.current_round.completed)

  @property
  def winner(self):
    if self.completed:
      return self.current_round.heats[0].winner
    return None

  def add_competitor(self, competitor):
    if not competitor in self.competitors:
      self.competitors.append(competitor)
      competitor.add_event(self)

  def draft(self):
    remaining_surfers = self.default_draft_order.copy()
    while len(remaining_surfers) > 0:
      for competitor in self.competitors:
        drafted_surfer = competitor.draft(self, remaining_surfers)
        del remaining_surfers[remaining_surfers.index(drafted_surfer)]
    self.has_drafted = True
  
  @property
  def default_draft_order(self):
    athletes_url = "{}/athletes/tour/mct?year={}".format(
      _HOMEPAGE_URL, self.year)
    athlete_soup = load_soup(athletes_url)
    names = athlete_soup.find_all('a', class_='athlete-name')
    return [name.text for name in names][:36]

  def score(self, competitor):
    score = 0
    for surfer in competitor.events[self]['team']:
      for round_ in self.rounds:
        # TODO: replace with real scoring function
        for heat in round_.heats:
          if surfer in heat.athlete_names:
            score += 1
            break
    return score


class Competitor(object):
  def __init__(self, name):
    self.name = name
    self.events = {}

  def add_event(self, event):
    if event not in self.events:
      self.events[event] = {
        'team': [], 'draft_order': event.default_draft_order}

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
