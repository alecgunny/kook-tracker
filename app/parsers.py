from app import client
import json


class EventNotReady(Exception):
  pass


def get_event_ids(season_url, event_names=None):
  '''
  Finds the WSL ids assigned to the given `event_names` for the season hosted
  at `season_url`
  Parameters
  -------------------------
  season_url: str
    a valid WSL website URL corresponding to the main page for a Men's Championship
    Tour season
  event_names: str or array_like(str) or None
    either a single string event name or an iterable of string event names for
    which to find ids. Valid events are those with links to event pages. If left
    as None, will find ids for all currently valid events in a season. Otherwise,
    if any specified events are not valid, a `ValueError` will be raised.

  Returns
  -------------------------
  event_ids: dict
    dictionary mapping event names to WSL assigned ids
  '''
  if isinstance(event_names, str):
    event_names = [event_names]

  soup = client(season_url)
  event_divs = soup.find_all('div', class_='tour-event-detail')
  event_ids = {}
  for div in event_divs:
    try:
      event_url = div.find('a').attrs['href']
    except AttributeError:
      continue

    event_id, event_name = event_url.split("/")[-2:]
    if event_names is None or event_name in event_names:
      event_ids[event_name] = event_id

  # if event names are specifically requested and they couldn't be found,
  # raise an error
  if (event_names is not None and
      any([name not in event_ids for name in event_names])):
    missing_names = [name for name in event_names if name not in event_ids]
    raise ValueError('Could not find events {}'.format(
      ', '.join(missing_names)))

  return event_ids


def get_round_ids(event_url):
  soup = client(event_url)
  round_link_divs = soup.find_all(
    'div', class_='post-event-watch-round-nav__item')
  if len(round_link_divs) == 0:
    raise EventNotReady

  round_ids = []
  for div in round_link_divs:
    round_ids.append(
      json.loads(div.find('a').attrs['data-gtm-event'])['round-ids'])
  return round_ids
