from collections import defaultdict
from dataclasses import dataclass

from app import app
from app.rosters import rosters, year_long_picks


@dataclass
class Kook:
    name: str
    color: str

    def __post_init__(self):
        self.rosters = defaultdict(dict)
        self.year_longs = defaultdict(dict)

    def add_roster(self, season, event, athletes):
        self.rosters[season][event] = athletes

    def add_year_long(self, season, event, athlete):
        self.year_longs[season][event] = athlete


ranch_scores = {
    2023: {
        "Nick S": 4745,
        "Mike P": 4745,
        "Charlie P": 10000,
        "Alex B": 1330,
        "RJ D": 4745,
        "Rocky F": 3320,
        "Kurt D": 6085,
        "Alec G": 7800,
        "Dusty D": 3320,
    }
}

palette = [
    "#ed1c24",
    "#ff6600",
    "#235789",
    "#f1d302",
    "#020100",
    "#71816d",
    "#0ead69",
    "#9593d9",
    "#ae76a6",
    "#9593d9",
    "#9593d9",
    "#9593d9",
]

kook_names = [
    "Alex B",
    "Charlie P",
    "Dusty D",
    "Alec G",
    "Rocky F",
    "Mike P",
    "Nick S",
    "Charlie B",
    "Kurt D",
    "Mick U",
    "Andrew H",
    "RJ D",
]

kooks = [Kook(name, color) for name, color in zip(kook_names, palette)]
for year, events in rosters.items():
    for event, rstrs in events.items():
        for kook in kooks:
            try:
                roster = rstrs[kook.name]
            except KeyError:
                continue
            kook.add_roster(year, event, roster)

            try:
                year_long = year_long_picks[year][event]
            except KeyError:
                app.logger.warn(
                    "Missing year long picks for event {} {}".format(
                        year, event
                    )
                )
                continue

            try:
                pick = year_long[kook.name]
            except KeyError:
                raise ValueError(
                    f"Kook {kook.name} has no pick for event {event}"
                )
            kook.add_year_long(year, event, pick)
