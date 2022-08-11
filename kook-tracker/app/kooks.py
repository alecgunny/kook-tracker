from collections import defaultdict
from dataclasses import dataclass

from app import app


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


rosters = {
    2021: {
        "billabong-pipe-masters-presented-by-hydro-flask": {
            "Alex B": [
                "John John Florence",
                "Adriano de Souza",
                "Caio Ibelli",
                "Alex Ribeiro",
            ],
            "Charlie P": [
                "John John Florence",
                "Adriano de Souza",
                "Caio Ibelli",
                "Alex Ribeiro",
            ],
            "Dusty D": [
                "Kelly Slater",
                "Yago Dora",
                "Ryan Callinan",
                "Miguel Pupo",
            ],
            "Alec G": [
                "Filipe Toledo",
                "Conner Coffin",
                "Deivid Silva",
                "Morgan Cibilic",
            ],
            "Rocky F": [
                "Jordy Smith",
                "Julian Wilson",
                "Frederico Morais",
                "Peterson Crisanto",
            ],
            "Mike P": [
                "Kolohe Andino",
                "Jeremy Flores",
                "Matthew McGillivray",
                "Wade Carmichael",
            ],
            "Nick S": [
                "Jack Robinson",
                "Seth Moniz",
                "Leonardo Fioravanti",
                "Ethan Ewing",
            ],
            "Charlie B": [
                "Italo Ferreira",
                "Jack Freestone",
                "Mikey Wright",
                "Miguel Tudela",
            ],
            "Kurt D": [
                "Sebastian Zietz",
                "Michel Bourez",
                "Griffin Colapinto",
                "Jadson Andre",
            ],
        },
        "rip-curl-newcastle-cup-presented-by-corona": {
            "Rocky F": [
                "John John Florence",
                "Wade Carmichael",
                "Caio Ibelli",
                "Alex Ribeiro",
            ],
            "Nick S": [
                "Italo Ferreira",
                "Jack Freestone",
                "Ethan Ewing",
                "Matt Banting",
            ],
            "Mike P": [
                "Jordy Smith",
                "Yago Dora",
                "Matthew McGillivray",
                "Jackson Baker",
            ],
            "Kurt D": [
                "Filipe Toledo",
                "Mikey Wright",
                "Seth Moniz",
                "Adriano de Souza",
            ],
            "Dusty D": [
                "Gabriel Medina",
                "Jeremy Flores",
                "Adrian Buchan",
                "Miguel Pupo",
            ],
            "Charlie B": [
                "Julian Wilson",
                "Owen Wright",
                "Connor O'Leary",
                "Leonardo Fioravanti",
            ],
            "Charlie P": [
                "Griffin Colapinto",
                "Jack Robinson",
                "Frederico Morais",
                "Michel Bourez",
            ],
            "Alex B": [
                "Conner Coffin",
                "Morgan Cibilic",
                "Jadson Andre",
                "Peterson Crisanto",
            ],
            "Alec G": [
                "Kanoa Igarashi",
                "Ryan Callinan",
                "Deivid Silva",
                "Crosby Colapinto",
            ],
        },
        "rip-curl-narrabeen-classic-presented-by-corona": {
            "Rocky F": [
                "Owen Wright",
                "Jack Robinson",
                "Caio Ibelli",
                "Connor O'Leary",
            ],
            "Nick S": [
                "Italo Ferreira",
                "Wade Carmichael",
                "Reef Heazlewood",
                "Dylan Moffat",
            ],
            "Mike P": [
                "Gabriel Medina",
                "Yago Dora",
                "Jeremy Flores",
                "Matthew McGillivray",
            ],
            "Kurt D": [
                "John John Florence",
                "Ryan Callinan",
                "Leonardo Fioravanti",
                "Peterson Crisanto",
            ],
            "Dusty D": [
                "Filipe Toledo",
                "Griffin Colapinto",
                "Mikey Wright",
                "Miguel Pupo",
            ],
            "Mick U": [
                "Jordy Smith",
                "Julian Wilson",
                "Deivid Silva",
                "Ethan Ewing",
            ],
            "Charlie P": [
                "Mick Fanning",
                "Jack Freestone",
                "Seth Moniz",
                "Michel Bourez",
            ],
            "Alex B": [
                "Conner Coffin",
                "Alex Ribeiro",
                "Frederico Morais",
                "Jadson Andre",
            ],
            "Alec G": [
                "Kanoa Igarashi",
                "Morgan Cibilic",
                "Adriano de Souza",
                "Adrian Buchan",
            ],
        },
        "boost-mobile-margaret-river-pro-presented-by-corona": {
            "Kurt D": [
                "John John Florence",
                "Adriano de Souza",
                "Jeremy Flores",
                "Cyrus Cox",
            ],
            "Dusty D": [
                "Gabriel Medina",
                "Yago Dora",
                "Michel Bourez",
                "Deivid Silva",
            ],
            "Mick U": [
                "Italo Ferreira",
                "Frederico Morais",
                "Ethan Ewing",
                "Peterson Crisanto",
            ],
            "Charlie P": [
                "Filipe Toledo",
                "Griffin Colapinto",
                "Wade Carmichael",
                "Miguel Pupo",
            ],
            "Alex B": [
                "Julian Wilson",
                "Jordy Smith",
                "Adrian Buchan",
                "Alex Ribeiro",
            ],
            "Alec G": [
                "Kanoa Igarashi",
                "Conner Coffin",
                "Morgan Cibilic",
                "Jadson Andre",
            ],
            "Rocky F": [
                "Owen Wright",
                "Jack Freestone",
                "Connor O'Leary",
                "Matthew McGillivray",
            ],
            "Nick S": [
                "Jack Robinson",
                "Ryan Callinan",
                "Reef Heazlewood",
                "Jacob Willcox",
            ],
            "Mike P": [
                "Seth Moniz",
                "Mikey Wright",
                "Caio Ibelli",
                "Leonardo Fioravanti",
            ],
        },
        "rip-curl-rottnest-search-presented-by-corona": {
            "Kurt D": [
                "Jeremy Flores",
                "Yago Dora",
                "Taj Burrow",
                "Ethan Ewing",
            ],
            "Dusty D": [
                "Filipe Toledo",
                "Wade Carmichael",
                "Deivid Silva",
                "Miguel Pupo",
            ],
            "Mick U": [
                "Gabriel Medina",
                "Caio Ibelli",
                "Connor O'Leary",
                "Liam O'Brien",
            ],
            "Charlie P": [
                "Italo Ferreira",
                "Jack Freestone",
                "Jadson Andre",
                "Leonardo Fioravanti",
            ],
            "Alex B": [
                "Jordy Smith",
                "Frederico Morais",
                "Michel Bourez",
                "Adriano de Souza",
            ],
            "Alec G": [
                "Conner Coffin",
                "Owen Wright",
                "Mikey Wright",
                "Jacob Willcox",
            ],
            "Rocky F": [
                "Griffin Colapinto",
                "Morgan Cibilic",
                "Alex Ribeiro",
                "Stuart Kennedy",
            ],
            "Nick S": [
                "Jack Robinson",
                "Seth Moniz",
                "Julian Wilson",
                "Kael Walsh",
            ],
            "Mike P": [
                "Kanoa Igarashi",
                "Ryan Callinan",
                "Matthew McGillivray",
                "Peterson Crisanto",
            ],
        },
    },
    2022: {
        "billabong-pro-pipeline": {
            "Nick S": [
                "John John Florence",
                "Imaikalani deVault",
                "Jake Marshall",
                "Lucca Mesinas",
            ],
            "Mike P": [
                "Italo Ferreira",
                "Seth Moniz",
                "Jackson Baker",
                "Joao Chianca",
            ],
            "Charlie P": [
                "Filipe Toledo",
                "Morgan Cibilic",
                "Connor O'Leary",
                "Miguel Tudela",
            ],
            "Alex B": [
                "Griffin Colapinto",
                "Ezekiel Lau",
                "Frederico Morais",
                "Callum Robson",
            ],
            "Andrew H": [
                "Kanoa Igarashi",
                "Ivan Florence",
                "Ethan Ewing",
                "Samuel Pupo",
            ],
            "Rocky F": [
                "Owen Wright",
                "Nat Young",
                "Leonardo Fioravanti",
                "Jordan Lawler",
            ],
            "Kurt D": [
                "Jack Robinson",
                "Jordy Smith",
                "Caio Ibelli",
                "Jadson Andre",
            ],
            "Alec G": [
                "Kolohe Andino",
                "Conner Coffin",
                "Matthew McGillivray",
                "Carlos Munoz",
            ],
            "Dusty D": [
                "Kelly Slater",
                "Barron Mamiya",
                "Miguel Pupo",
                "Deivid Silva",
            ],
        },
        "hurley-pro-sunset-beach": {
            "Mike P": [
                "John John Florence",
                "Billy Kemper",
                "Filipe Toledo",
                "Jordan Lawler",
            ],
            "Charlie P": [
                "Italo Ferreira",
                "Koa Smith",
                "Joao Chianca",
                "Jackson Baker",
            ],
            "Alex B": [
                "Miguel Pupo",
                "Caio Ibelli",
                "Nat Young",
                "Connor O'Leary",
            ],
            "Andrew H": [
                "Seth Moniz",
                "Ethan Ewing",
                "Callum Robson",
                "Jake Marshall",
            ],
            "Rocky F": [
                "Conner Coffin",
                "Leonardo Fioravanti",
                "Frederico Morais",
                "Jadson Andre",
            ],
            "Kurt D": [
                "Jordy Smith",
                "Morgan Cibilic",
                "Lucca Mesinas",
                "Deivid Silva",
            ],
            "Alec G": [
                "Kanoa Igarashi",
                "Kolohe Andino",
                "Ryan Callinan",
                "Samuel Pupo",
            ],
            "Dusty D": [
                "Jack Robinson",
                "Kelly Slater",
                "Griffin Colapinto",
                "Matthew McGillivray",
            ],
            "Nick S": [
                "Ezekiel Lau",
                "Barron Mamiya",
                "Owen Wright",
                "Imaikalani deVault",
            ],
        },
        "meo-portugal-pro": {
            "Charlie P": [
                "John John Florence",
                "Joao Chianca",
                "Kolohe Andino",
                "Afonso Antunes",
            ],
            "Alex B": [
                "Miguel Pupo",
                "Caio Ibelli",
                "Nat Young",
                "Justin Becret",
            ],
            "Andrew H": [
                "Italo Ferreira",
                "Ezekiel Lau",
                "Seth Moniz",
                "Connor O'Leary",
            ],
            "Rocky F": [
                "Filipe Toledo",
                "Owen Wright",
                "Leonardo Fioravanti",
                "Vasco Ribeiro",
            ],
            "Kurt D": [
                "Jack Robinson",
                "Griffin Colapinto",
                "Samuel Pupo",
                "Deivid Silva",
            ],
            "Alec G": [
                "Kanoa Igarashi",
                "Conner Coffin",
                "Morgan Cibilic",
                "Matthew McGillivray",
            ],
            "Dusty D": [
                "Jordy Smith",
                "Jake Marshall",
                "Jackson Baker",
                "Jadson Andre",
            ],
            "Nick S": [
                "Kelly Slater",
                "Ethan Ewing",
                "Ryan Callinan",
                "Callum Robson",
            ],
            "Mike P": [
                "Barron Mamiya",
                "Frederico Morais",
                "Imaikalani deVault",
                "Lucca Mesinas",
            ],
        },
        "rip-curl-pro-bells-beach": {
            "Alex B": [
                "Kanoa Igarashi",
                "Kelly Slater",
                "Caio Ibelli",
                "Tully Wylie",
            ],
            "Andrew H": [
                "Griffin Colapinto",
                "Connor O'Leary",
                "Nat Young",
                "Deivid Silva",
            ],
            "Rocky F": [
                "Filipe Toledo",
                "Owen Wright",
                "Jadson Andre",
                "Imaikalani deVault",
            ],
            "Kurt D": [
                "John John Florence",
                "Seth Moniz",
                "Mick Fanning",
                "Callum Robson",
            ],
            "Alec G": [
                "Italo Ferreira",
                "Miguel Pupo",
                "Leonardo Fioravanti",
                "Matthew McGillivray",
            ],
            "Dusty D": [
                "Jordy Smith",
                "Ezekiel Lau",
                "Morgan Cibilic",
                "Lucca Mesinas",
            ],
            "Nick S": [
                "Jack Robinson",
                "Ethan Ewing",
                "Jake Marshall",
                "Samuel Pupo",
            ],
            "Mike P": [
                "Kolohe Andino",
                "Barron Mamiya",
                "Joao Chianca",
                "Mikey Wright",
            ],
            "Charlie P": [
                "Ryan Callinan",
                "Conner Coffin",
                "Frederico Morais",
                "Jackson Baker",
            ],
        },
        "margaret-river-pro": {
            "Andrew H": [
                "John John Florence",
                "Nat Young",
                "Seth Moniz",
                "Jack Thomas",
            ],
            "Rocky F": [
                "Kanoa Igarashi",
                "Miguel Pupo",
                "Joao Chianca",
                "Jacob Willcox",
            ],
            "Kurt D": [
                "Filipe Toledo",
                "Owen Wright",
                "Ezekiel Lau",
                "Jadson Andre",
            ],
            "Alec G": [
                "Italo Ferreira",
                "Griffin Colapinto",
                "Matthew McGillivray",
                "Deivid Silva",
            ],
            "Dusty D": [
                "Ethan Ewing",
                "Caio Ibelli",
                "Jackson Baker",
                "Lucca Mesinas",
            ],
            "Nick S": [
                "Jack Robinson",
                "Barron Mamiya",
                "Jake Marshall",
                "Leonardo Fioravanti",
            ],
            "Mike P": [
                "Jordy Smith",
                "Kolohe Andino",
                "Conner Coffin",
                "Imaikalani deVault",
            ],
            "Charlie P": [
                "Ryan Callinan",
                "Morgan Cibilic",
                "Frederico Morais",
                "Samuel Pupo",
            ],
            "Alex B": [
                "Callum Robson",
                "Kelly Slater",
                "Connor O'Leary",
                "Ben Spence",
            ],
        },
        "quiksilverroxy-pro-g-land": {
            "Rocky F": [
                "John John Florence",
                "Connor O'Leary",
            ],
            "Kurt D": [
                "Italo Ferreira",
                "Caio Ibelli",
            ],
            "Alec G": [
                "Filipe Toledo",
                "Matthew McGillivray",
            ],
            "Dusty D": [
                "Jack Robinson",
                "Kolohe Andino",
            ],
            "Nick S": [
                "Gabriel Medina",
                "Rio Waida",
            ],
            "Mike P": [
                "Kelly Slater",
                "Ethan Ewing",
            ],
            "Charlie P": [
                "Kanoa Igarashi",
                "Griffin Colapinto",
            ],
            "Alex B": [
                "Jadson Andre",
                "Jordy Smith",
            ],
            "Andrew H": [
                "Nat Young",
                "Miguel Pupo",
            ],
        },
        "surf-city-el-salvador-pro": {
            "Kurt D": [
                "Italo Ferreira",
                "Kolohe Andino",
            ],
            "Alec G": [
                "Jack Robinson",
                "Matthew McGillivray",
            ],
            "Dusty D": [
                "Kanoa Igarashi",
                "Caio Ibelli",
            ],
            "Nick S": [
                "Filipe Toledo",
                "Ethan Ewing",
            ],
            "Mike P": [
                "Miguel Pupo",
                "Griffin Colapinto",
            ],
            "Charlie P": [
                "Yago Dora",
                "Gabriel Medina",
            ],
            "Alex B": [
                "Carlos Munoz",
                "Callum Robson",
            ],
            "Andrew H": [
                "Connor O'Leary",
                "Nat Young",
            ],
            "Rocky F": [
                "Samuel Pupo",
                "Jordy Smith",
            ],
        },
        "oi-rio-pro": {
            "Alec G": [
                "Filipe Toledo",
                "Callum Robson",
            ],
            "Dusty D": [
                "Italo Ferreira",
                "Michael Rodrigues",
            ],
            "Nick S": [
                "Gabriel Medina",
                "Caio Ibelli",
            ],
            "Mike P": [
                "Jack Robinson",
                "Yago Dora",
            ],
            "Charlie P": [
                "Griffin Colapinto",
                "Ethan Ewing",
            ],
            "Alex B": [
                "Connor O'Leary",
                "Nat Young",
            ],
            "Andrew H": [
                "Kanoa Igarashi",
                "Matthew McGillivray",
            ],
            "Rocky F": [
                "Miguel Pupo",
                "Jake Marshall",
            ],
            "Kurt D": [
                "Kolohe Andino",
                "Joao Chianca",
            ],
        },
        "corona-open-j-bay": {
            "Dusty D": [
                "Filipe Toledo",
                "Matthew McGillivray",
            ],
            "Nick S": [
                "Jack Robinson",
                "Seth Moniz",
            ],
            "Mike P": [
                "Italo Ferreira",
                "Kolohe Andino",
            ],
            "Charlie P": [
                "Kanoa Igarashi",
                "Jordy Smith",
            ],
            "Alex B": [
                "Connor O'Leary",
                "Kelly Slater",
            ],
            "Andrew H": [
                "Luke Thompson",
                "Nat Young",
            ],
            "Rocky F": [
                "Jadson Andre",
                "Barron Mamiya",
            ],
            "Kurt D": [
                "Joshe Faulkner",
                "Samuel Pupo",
            ],
            "Alec G": [
                "Griffin Colapinto",
                "Ethan Ewing",
            ],
        },
        "outerknown-tahiti-pro": {
            "Nick S": [
                "Jack Robinson",
                "Kauli Vaast",
            ],
            "Mike P": [
                "Filipe Toledo",
                "Yago Dora",
            ],
            "Charlie P": [
                "Italo Ferreira",
                "Caio Ibelli",
            ],
            "Alex B": [
                "Nat Young",
                "Michel Bourez",
            ],
            "Andrew H": [
                "Griffin Colapinto",
                "Samuel Pupo",
            ],
            "Rocky F": [
                "Miguel Pupo",
                "Matthew McGillivray",
            ],
            "Kurt D": [
                "Seth Moniz",
                "Jordy Smith",
            ],
            "Alec G": [
                "Kanoa Igarashi",
                "Ethan Ewing",
            ],
            "Dusty D": [
                "Kelly Slater",
                "Barron Mamiya",
            ],
        },
    },
}

year_long_picks = {
    2022: {
        "billabong-pro-pipeline": {
            "Nick S": "John John Florence",
            "Mike P": "Italo Ferreira",
            "Charlie P": "Italo Ferreira",
            "Alex B": "John John Florence",
            "Andrew H": "John John Florence",
            "Rocky F": "John John Florence",
            "Kurt D": "John John Florence",
            "Alec G": "John John Florence",
            "Dusty D": "John John Florence",
        },
        "hurley-pro-sunset-beach": {
            "Nick S": "John John Florence",
            "Mike P": "Jack Robinson",
            "Charlie P": "John John Florence",
            "Alex B": "Miguel Pupo",
            "Andrew H": "John John Florence",
            "Rocky F": "John John Florence",
            "Kurt D": "John John Florence",
            "Alec G": "Kolohe Andino",
            "Dusty D": "John John Florence",
        },
        "meo-portugal-pro": {
            "Nick S": "Italo Ferreira",
            "Mike P": "Jack Robinson",
            "Charlie P": "John John Florence",
            "Alex B": "Miguel Pupo",
            "Andrew H": "Kanoa Igarashi",
            "Rocky F": "John John Florence",
            "Kurt D": "Filipe Toledo",
            "Alec G": "Filipe Toledo",
            "Dusty D": "John John Florence",
        },
        "rip-curl-pro-bells-beach": {
            "Nick S": "Griffin Colapinto",
            "Mike P": "Filipe Toledo",
            "Charlie P": "Jack Robinson",
            "Alex B": "John John Florence",
            "Andrew H": "Kanoa Igarashi",
            "Rocky F": "John John Florence",
            "Kurt D": "Filipe Toledo",
            "Alec G": "Filipe Toledo",
            "Dusty D": "John John Florence",
        },
        "margaret-river-pro": {
            "Nick S": "John John Florence",
            "Mike P": "John John Florence",
            "Charlie P": "Jack Robinson",
            "Alex B": "John John Florence",
            "Andrew H": "Kelly Slater",
            "Rocky F": "John John Florence",
            "Kurt D": "John John Florence",
            "Alec G": "John John Florence",
            "Dusty D": "John John Florence",
        },
        "quiksilverroxy-pro-g-land": {
            "Nick S": "John John Florence",
            "Mike P": "Italo Ferreira",
            "Charlie P": "Gabriel Medina",
            "Alex B": "Jack Robinson",
            "Andrew H": "Kelly Slater",
            "Rocky F": "John John Florence",
            "Kurt D": "Italo Ferreira",
            "Alec G": "Italo Ferreira",
            "Dusty D": "John John Florence",
        },
        "surf-city-el-salvador-pro": {
            "Nick S": "Filipe Toledo",
            "Mike P": "Filipe Toledo",
            "Charlie P": "Filipe Toledo",
            "Alex B": "Jack Robinson",
            "Andrew H": "Kelly Slater",
            "Rocky F": "John John Florence",
            "Kurt D": "Italo Ferreira",
            "Alec G": "Gabriel Medina",
            "Dusty D": "Jack Robinson",
        },
        "oi-rio-pro": {
            "Nick S": "Filipe Toledo",
            "Mike P": "Filipe Toledo",
            "Charlie P": "Gabriel Medina",
            "Alex B": "Gabriel Medina",
            "Andrew H": "Filipe Toledo",
            "Rocky F": "John John Florence",
            "Kurt D": "Filipe Toledo",
            "Alec G": "Filipe Toledo",
            "Dusty D": "Kanoa Igarashi",
        },
        "corona-open-j-bay": {
            "Nick S": "Jack Robinson",
            "Mike P": "Jack Robinson",
            "Charlie P": "Gabriel Medina",
            "Alex B": "Connor O'Leary",
            "Andrew H": "Filipe Toledo",
            "Rocky F": "John John Florence",
            "Kurt D": "Filipe Toledo",
            "Alec G": "Jack Robinson",
            "Dusty D": "Kanoa Igarashi",
        },
        "outerknown-tahiti-pro": {
            "Nick S": "Jack Robinson",
            "Mike P": "Italo Ferreira",
            "Charlie P": "Kelly Slater",
            "Alex B": "Filipe Toledo",
            "Andrew H": "Filipe Toledo",
            "Rocky F": "Italo Ferreira",
            "Kurt D": "Seth Moniz",
            "Alec G": "Jack Robinson",
            "Dusty D": "Kelly Slater",
        },
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
