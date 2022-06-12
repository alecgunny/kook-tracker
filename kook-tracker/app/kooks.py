from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Kook:
    name: str
    color: str

    def __attrs_post_init__(self):
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
        "meo-pro-portugal": {
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
    },
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
