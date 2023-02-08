import datetime
import json
import re
from collections import defaultdict

from config import Config

from app import client

_MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


# =============================================================================
#                         Utilities
# =============================================================================
class EventNotReady(Exception):
    pass


def _get_date(year, month, day):
    return datetime.datetime.strptime(
        "{}-{}-{}".format(year, month, day), "%Y-%m-%d"
    )


# =============================================================================
#                      Season Page Parsers
# =============================================================================
def get_season_url(season):
    return f"{Config.MAIN_URL}/events/{season.year}/mct?all=1"


def get_event_data_from_season_homepage(season_url):
    url_split = season_url.split("/")
    year = int(url_split[url_split.index("events") + 1])

    soup = client(season_url)
    event_table = soup.find("table", class_="tableType-event")
    even_rows = event_table.find_all("tr", class_="even")
    odd_rows = event_table.find_all("tr", class_="odd")
    if len(even_rows) < len(odd_rows):
        even_rows.append(None)
    rows = [row for pair in zip(odd_rows, even_rows) for row in pair if row]

    data = []
    for row in rows:
        id = int(row.attrs["class"][0].split("-")[1])

        # TODO: dealing with the year here is nontrivial if it
        # occurs in the year before or after the intended season
        # (e.g. first event of 2021 season is in Dec. 2020),
        # since it's included with the month headers grouping events.
        # I don't think we ever use it, so I'm not too worried about
        # it at the moment, but could be problematic down the line
        # so noting for posterity
        month, start_day, _ = row.find(
            "td", class_="event-date-range"
        ).text.split(maxsplit=2)

        month = _MONTHS.index(month) + 1
        start_date = _get_date(year, month, start_day)

        status = (
            row.find("span", class_="event-status").find("span").text.lower()
        )

        link = row.find("a", class_="event-schedule-details__event-name")
        if link is not None:
            link = link.attrs["href"]
        data.append(
            {
                "id": id,
                "start_date": start_date,
                "status": status,
                "link": link,
            }
        )
    return data


def get_event_ids(season_url, event_names=None):
    """
    Finds the WSL ids assigned to the given `event_names` for the season hosted
    at `season_url`
    Parameters
    -------------------------
    season_url: str
        a valid WSL website URL corresponding to the main page for a Men's
        Championship Tour season
    event_names: str or array_like(str) or None
        either a single string event name or an iterable of string
        event names for which to find ids. Valid events are those
        with links to event pages. If left as None, will find ids
        for all currently valid events in a season. Otherwise, if
        any specified events are not valid, a `ValueError` will be
        raised

    Returns
    -------------------------
    event_ids: dict
        dictionary mapping event names to WSL assigned ids
    """

    if isinstance(event_names, str):
        event_names = [event_names]

    event_data = get_event_data_from_season_homepage(season_url)
    event_ids = {}
    for data in event_data:
        if data["link"] is None:
            continue

        for i in range(2):
            try:
                event_id, event_name = data["link"].split("/")[-3:-1]
                event_id = int(event_id)
            except ValueError as exc:
                if "invalid literal" in str(exc) and i == 0:
                    soup = client(data["link"])
                    header = soup.find("h1", class_="event-information__title")
                    link = header.find("a")
                    data["link"] = link.attrs["href"]
                else:
                    raise
            else:
                if event_names is None or event_name in event_names:
                    event_ids[event_name] = event_id
                break
        else:
            raise ValueError(
                "Event link with start date {} has broken link {}".format(
                    data["start_date"], data["link"]
                )
            )

    # if event names are specifically requested
    # and they couldn't be found, raise an error
    if event_names is not None and any(
        [name not in event_ids for name in event_names]
    ):
        missing_names = [name for name in event_names if name not in event_ids]
        raise ValueError(
            "Could not find valid links for events {}".format(
                ", ".join(missing_names)
            )
        )

    return event_ids


# =============================================================================
#                    Event Page parsers
# =============================================================================
def get_event_url(event):
    return Config.MAIN_URL + "/events/{}/ct/{}/{}".format(
        event.season.year, event.id, event.name
    )


def get_event_data_from_event_homepage(event_url):
    url_split = event_url.split("/")
    year = int(url_split[url_split.index("events") + 1])
    soup = client(event_url)

    try:
        event_status = (
            soup.find("span", class_="status-module__status")
            .text.strip("\n")
            .lower()
        )
    except AttributeError:
        if soup.find("div", id="live-strip") is not None:
            return "live", datetime.datetime.now()
        else:
            raise ValueError("Event homepage is off")

    # we don't actually need the start date if the event
    # has already started to just return a dummy date
    if event_status == "live":
        return event_status, datetime.datetime.now()

    month, start_day, year = soup.find(
        "span", class_="event-information__meta-item--date-range"
    ).text.split(maxsplit=2)
    month = _MONTHS.index(month) + 1
    year = year.split(",")[-1].strip()
    start_date = _get_date(year, month, start_day)

    return event_status, start_date


# =============================================================================
#                       Round Page parsers
# =============================================================================
def get_round_url(round_):
    return round_.event.url + "/results?roundId=" + str(round_.id)


def get_round_ids(event_url):
    soup = client(event_url)
    round_link_divs = soup.find_all(
        "div", class_="post-event-watch-round-nav__item"
    )

    if len(round_link_divs) == 0:
        raise EventNotReady

    round_ids = []
    for div in round_link_divs:
        link = div.find("a")
        try:
            metadata = link.attrs["data-gtm-event"]
        except KeyError:
            continue
        else:
            metadata = json.loads(metadata)

        round_id = metadata["slug"].split("-")[1]
        round_ids.append(int(round_id))

    if len(round_ids) == 0:
        raise ValueError(
            "Couldn't find any round ids in round divs:\n {}".format(
                "\n\n".join(map(str, round_link_divs))
            )
        )

    return round_ids


def find_heat_divs(round_url, heat_id=None):
    attrs = {"data-heat-id": heat_id} if heat_id is not None else heat_id
    divs = client(round_url).find_all(
        "div", class_="post-event-watch-heat-grid__heat", attrs=attrs
    )
    if heat_id is None:
        return divs
    return divs[0]


def get_heat_ids(round_url):
    heat_divs = find_heat_divs(round_url)
    return [int(div.attrs["data-heat-id"]) for div in heat_divs]


def get_heat_status(heat_div):
    for cls in heat_div.attrs["class"]:
        match = re.search(r"(?<=--status-)\w+$", cls)
        if match is not None:
            status = match.group(0)
            break
    else:
        return 0

    if status == "upcoming":
        return 0
    elif status == "over":
        return 2
    else:
        return 1


def get_heat_data(round_url, heat_id):
    heat_div = find_heat_divs(round_url, heat_id)
    status = get_heat_status(heat_div)

    # next get athlete names and scores
    athlete_divs = heat_div.find_all(
        "div", class_="hot-heat-athlete__name--full"
    )

    scores = []
    for div in athlete_divs:
        athlete_name = div.text
        names = athlete_name.split()
        athlete_name = names[0][0] + ". " + names[-1]
        score = div.find_next_sibling(
            "div", class_="hot-heat-athlete__score"
        ).text

        # if score isn't a number, that's either because
        # the heat hasn't started or it has but the
        # athlete hasn't taken a wave yet. To differentiate
        # these, we'll use None for the former case and 0
        # for the latter and use status to decide which one to use
        try:
            score = round(float(score), 2)
        except ValueError:
            score = None if status == 0 else 0

        scores.append((athlete_name, score))
    return status, scores


def parse_bracket(round_url):
    soup = client(round_url)
    rounds = defaultdict(dict)
    columns = soup.find_all("div", class_="bracket-stage-round")
    for column in columns:
        heats = column.find_all(
            "div", class_="post-event-watch-heat-bracket-stage__heat"
        )
        for heat in heats:
            status = get_heat_status(heat)
            data = json.loads(heat.attrs["data-pickem-gtm"])
            heat_id = int(data["heat-ids"])
            round_id = int(data["round-ids"])

            results = []
            names = heat.find_all("div", class_="hot-heat-athlete__name")
            scores = heat.find_all("div", class_="hot-heat-athlete__score")
            for name, score in zip(names, scores):
                try:
                    score = float(score.text)
                except ValueError:
                    score = None if not status else 0
                results.append((name.text, score))
            rounds[round_id][heat_id] = (status, results)

    return rounds
