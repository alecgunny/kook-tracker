from app import config, db, parsers
from app.models import wsl


def create_season(year):
    season = wsl.Season(year=year)
    db.session.add(season)

    season_url = "{}/events/{}/mct".format(config.MAIN_URL, year)
    event_ids = parsers.get_event_ids(season_url)
    for event_name, event_id in event_ids.items():
        if event_name != "freshwater-pro":  # ignore the ranch for now
            create_event(season, event_name, event_id)


def create_event(season, name, id):
    event = wsl.Event(id=id, name=name, season=season)

    try:
        event_url = "{}/events/{}/mct/{}/{}/results".format(
            config.MAIN_URL, event.season.year, event.id, event.name
        )
    except parsers.EventNotReady:
        return
    db.session.add(event)
    round_ids = parsers.get_round_ids(event_url)
    for round_num, round_id in enumerate(round_ids):
        create_round(event, round_id, round_num)

    if all([round_.completed for round_ in event.rounds]):
        event.completed = True


def create_round(event, round_id, round_num):
    round_ = wsl.Round(id=round_id, number=round_num, event=event)
    db.session.add(round_)
