palette = [
    "ed1c24",
    "ff6600",
    "235789",
    "f1d302",
    "020100",
    "71816d",
    "0ead69",
    "9593d9",
    "ae76a6",
]
palette = ["#" + x for x in palette]

kooks = {
    "Alex B": {
        "athletes": [
            # "Gabriel Medina",
            # "Michel Bourez",
            # "Wade Carmichael",
            # "Jesse Mendes"
            "John John Florence",
            "Adriano de Souza",
            "Caio Ibelli",
            "Alex Ribeiro",
        ]
    },
    "Charlie P": {
        "athletes": [
            # "Owen Wright",
            # "Kelly Slater",
            # "Ricardo Christie",
            # "Peterson Crisanto"
            "Gabriel Medina",
            "Kanoa Igarashi",
            "Connor O'Leary",
            "Joshua Moniz",
        ]
    },
    "Dusty D": {
        "athletes": [
            # "John John Florence",
            # "Jeremy Flores",
            # "Michael Rodrigues",
            # "Deivid Silva"
            "Kelly Slater",
            "Yago Dora",
            "Ryan Callinan",
            "Miguel Pupo",
        ]
    },
    "Alec G": {
        "athletes": [
            # "Jordy Smith",
            # "Conner Coffin",
            # "Kanoa Igarashi",
            # "Willian Cardoso"
            "Filipe Toledo",
            "Conner Coffin",
            "Deivid Silva",
            # "Miguel Pupo",
            "Morgan Cibilic",
        ]
    },
    "Rocky F": {
        "athletes": [
            # "Filipe Toledo",
            # "Kolohe Andino",
            # "Caio Ibelli",
            # "Leonardo Fioravanti"
            "Jordy Smith",
            "Julian Wilson",
            "Frederico Morais",
            "Peterson Crisanto",
        ]
    },
    "Mike P": {
        "athletes": [
            # "Julian Wilson",
            # "Adrian Buchan",
            # "Ryan Callinan",
            # "Mateus Herdy"
            "Kolohe Andino",
            "Jeremy Flores",
            "Matthew McGillivray",
            "Wade Carmichael",
        ]
    },
    "Nick S": {
        "athletes": [
            # "Italo Ferreira",
            # "Seth Moniz",
            # "Soli Bailey",
            # "Reef Heazlewood"
            "Jack Robinson",
            "Seth Moniz",
            # "Event seed #34",
            "Leonardo Fioravanti",
            "Ethan Ewing",
        ]
    },
    "Charlie B": {
        "athletes": [
            # "Ezekiel Lau",
            # "Griffin Colapinto",
            # "Joan Duru",
            # "Jadson Andre"
            "Italo Ferreira",
            "Jack Freestone",
            # "Adrian Buchan",
            "Mikey Wright",
            "Miguel Tudela",
        ]
    },
    "Kurt D": {
        "athletes": [
            # "Mikey Wright",
            # "Jack Freestone",
            # "Yago Dora",
            "Sebastian Zietz",
            # "Owen Wright",
            "Michel Bourez",
            "Griffin Colapinto",
            "Jadson Andre",
        ]
    },
}

for (kook, attrs), color in zip(kooks.items(), palette):
    attrs["color"] = color
