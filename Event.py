import urllib
from bs4 import BeautifulSoup as bs
import itertools
import json


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
  def __init__(self, base_url):
    self.base_url = base_url+"/results"
    results_soup = load_soup(self.base_url)
    first_round_link = results_soup.find(
      'div', class_='post-event-watch-round-nav__item').find('a')
    round_data = json.loads(first_round_link.attrs['data-gtm-event'])
    self.initial_round_id = int(round_data['round-ids'])
    self.rounds = [Round(self.get_round_url(0))]
    self.update_rounds()

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
