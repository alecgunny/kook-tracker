# import os
# from ebcli.lib import elasticbeanstalk

# os.environ["AWS_DEFAULT_REGION"] = "us-west-1"
# env = elasticbeanstalk.get_environment(env_name="pipedream")

import argparse
import json
from datetime import datetime
from typing import Optional

import requests


def main(host: str, event_name: Optional[str] = None) -> None:
    year = datetime.now().year
    if event_name is None:
        with open("kook-tracker/app/rosters/teams.json", "r") as f:
            event_name = list(json.load(f)[str(year)])[-1]

    response = requests.get(
        f"http://{host}/event-results",
        params={"name": event_name, "year": str(year)},
    )
    response.raise_for_status()
    print(response.content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost:5000")
    parser.add_argument("--event_name", type=str, default=None)
    args = parser.parse_args()
    main(**vars(args))
