import urllib
from bs4 import BeautifulSoup as bs
import itertools


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
    if not self.initialized:
      return False
    return all([heat.completed for heat in self.heats])

  @property
  def num_heats(self):
    if not self.initialized:
      return None
    return len(self.heats)

  @property
  def winners(self):
    if not self.initialized:
      return None
    return [heat.winner for heat in self.heats]

  @property
  def losers(self):
    if not self.initialized:
      return None
    return [heat.loser for heat in self.heats]
