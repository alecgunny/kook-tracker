import json
from pathlib import Path

roster_dir = Path(__file__).parent / "rosters"
rosters = json.loads((roster_dir / "teams.json").read_text())
year_long_picks = json.loads((roster_dir / "year_longs.json").read_text())
