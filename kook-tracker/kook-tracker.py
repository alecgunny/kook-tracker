from app import app, db
from app.models import wsl


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "Season": wsl.Season,
        "Event": wsl.Event,
        "Round": wsl.Round,
        "Heat": wsl.Heat,
        "Athlete": wsl.Athlete,
        "HeatResult": wsl.HeatResult,
    }
