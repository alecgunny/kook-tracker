from collections import defaultdict

import attr


@attr.s(auto_attribs=True)
class Kook:
    name: str
    color: str

    def __attrs_post_init__(self):
        self.rosters = defaultdict(dict)

    def add_roster(self, season, event, athletes):
        self.rosters[season][event] = athletes


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
        }
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
    "#9593d9"
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
    "Andrew H"
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
