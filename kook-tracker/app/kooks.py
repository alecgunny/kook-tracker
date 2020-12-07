palette = [
  "#3f0d12",
  "#a71d31",
  "#f1f0cc",
  "#d5bf86",
  "#8d775f",
  "#0075f2",
  "#096b72",
  "#ffb7c3",
  "#697a21"
]

kooks = {
    "Alex B": {
        "athletes": [
            "Gabriel Medina",
            "Michel Bourez",
            "Wade Carmichael",
            "Jesse Mendes"
        ]
    },
    "Charlie P": {
        "athletes": [
            "Owen Wright",
            "Kelly Slater",
            "Ricardo Christie",
            "Peterson Crisanto"
        ]
    },
    "Dusty D": {
        "athletes": [
            "John John Florence",
            "Jeremy Flores",
            "Michael Rodrigues",
            "Deivid Silva"
        ]
    },
    "Alec G": {
        "athletes": [
            "Jordy Smith",
            "Conner Coffin",
            "Kanoa Igarashi",
            "Willian Cardoso"
        ]
    },
    "Rocky F": {
        "athletes": [
            "Filipe Toledo",
            "Kolohe Andino",
            "Caio Ibelli",
            "Leonardo Fioravanti"
        ]
    },
    "Mike P": {
        "athletes": [
            "Julian Wilson",
            "Adrian Buchan",
            "Ryan Callinan",
            "Mateus Herdy"
        ]
    },
    "Nick S": {
        "athletes": [
            "Italo Ferreira",
            "Seth Moniz",
            "Soli Bailey",
            "Reef Heazlewood"
        ]
    },
    "Charlie B": {
        "athletes": [
            "Ezekiel Lau",
            "Griffin Colapinto",
            "Joan Duru",
            "Jadson Andre"
        ]
    },
    "Kurt D": {
        "athletes": [
            "Mikey Wright",
            "Jack Freestone",
            "Yago Dora",
            "Sebastian Zietz"
        ]
    }
}

for (kook, attrs), color in zip(kooks.items(), palette):
    attrs["color"] = color