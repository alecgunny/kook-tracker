import argparse
import json
import os
from contextlib import contextmanager
from datetime import datetime

from apiclient import discovery
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials


def read_sheet(
    sheet_id: str, table_name: str, data_range: str
) -> list[list[str]]:
    cred_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    creds = Credentials.from_service_account_file(cred_file)

    service = discovery.build("sheets", "v4", credentials=creds)
    sheets = service.spreadsheets()
    query = sheets.values().get(
        spreadsheetId=sheet_id, range=f"{table_name}!{data_range}"
    )
    result = query.execute()

    try:
        return result["values"]
    except KeyError:
        raise ValueError("No values retrieved!")


@contextmanager
def update_context(json_file: str):
    """
    Context manager which will load a dictionary from
    json, then write it back to the same file with any
    in-place changes made.
    """
    with open(json_file, "r") as f:
        content = json.load(f)
    yield content

    with open(json_file, "w") as f:
        json.dump(content, f, indent=4)


def update_json(filename: str, event_name: str, year: int, update: dict):
    """
    Load a json file to a dictionary, and add an entry
    mapping the given event name to the specified roster
    to the mapping for the given year. If that year doesn't
    exist in the file, create it.
    """

    with update_context(filename) as content:
        try:
            this_year = content[str(year)]
        except KeyError:
            content[str(year)] = {event_name: update}
        else:
            this_year[event_name] = update


def _is_valid_draft_row(row: str):
    return bool(row.strip()) and row != "#N/A"


def _scrub_draft_column(column: list[str]) -> list[str]:
    return list(filter(_is_valid_draft_row, column))


def update_team_rosters(year: int, event_name: str, sheet_id: str) -> None:
    """
    Read the draft orders from Google sheets then execute
    a snake draft to build rosters for the given event.
    Write the new rosters to our roster json.
    """
    rows = read_sheet(sheet_id, "Draft", "B2:J38")

    # kook names are the top row of the sheet, zip
    # these with their columns to build draft orders.
    # Cut out any invalid values
    kooks = rows.pop(0)
    draft_orders = dict(zip(kooks, map(list, zip(*rows))))
    draft_orders = {k: _scrub_draft_column(v) for k, v in draft_orders.items()}

    # initialize some empty rosters and fill them
    # out until the all the draft orders are empty
    rosters = {kook: [] for kook in kooks}
    while any(draft_orders.values()):
        for kook in kooks:
            # grab the athlete at the top of this kook's
            # current draft order and add it to their roster
            athlete = draft_orders[kook][0]
            rosters[kook].append(athlete)

            # now remove that athlete from the
            # draft order of _all_ kooks
            for order in draft_orders.values():
                try:
                    order.remove(athlete)
                except ValueError:
                    # if a kook filled their draft out incorrectly
                    # and are missing this athlete, skip them
                    continue

        num_remaining = max([len(i) for i in draft_orders.values()])
        if num_remaining < len(kooks):
            # if there aren't enough athletes left to ensure
            # all kooks have the same roster length, we're done
            break

        # once we've gone through all the kooks,
        # reverse their order to snake the draft
        kooks = kooks[::-1]

    # now write the roster
    fname = "kook-tracker/app/rosters/teams.json"
    update_json(fname, event_name, year, rosters)


def update_year_long(
    year: int, event_name: str, nickname: str, sheet_id: str
) -> None:
    # read the year long picks from the Google sheet
    # and parse out the kook names from the top row
    rows = read_sheet(sheet_id, "Year Long", "B3:J4")
    # kooks = [i for i in rows.pop(0) if i]

    # # find the row corresponding to this event by
    # # using its nickname in the index column, then
    # # parse out all the athletes for each kook in that row
    # row_idx = [i[0] for i in rows].index(nickname)
    # athletes = rows[row_idx][1::2]

    # zip these into a dictionary and add it on
    # to our year long picks tracking json
    fname = "kook-tracker/app/rosters/year_longs.json"
    year_long_picks = dict(zip(*rows))
    update_json(fname, event_name, year, year_long_picks)


def main(
    event_name: str,
    nickname: str,
    sheet_id: str,
) -> None:
    year = datetime.now().year
    update_team_rosters(year, event_name, sheet_id)
    update_year_long(year, event_name, nickname, sheet_id)


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("event_name", type=str)
    parser.add_argument("--nickname", type=str)
    parser.add_argument("--sheet_id", type=str, default=os.getenv("SHEET_ID"))

    args = parser.parse_args()
    main(**vars(args))
