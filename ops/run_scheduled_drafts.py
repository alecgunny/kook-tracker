"""Hourly cron: drafts events and sends email reminders before each draft.

Idempotent — drafted events and sent reminders are tracked in JSON files
committed back to the repo, so the workflow is safe to re-run / catch up.

Testing flags:
    --dry-run        Skip Sheets, SMTP, and file writes;
                     print what would happen.
    --today DATE     Pretend now is the given UTC time (YYYY-MM-DD or
                     YYYY-MM-DDTHH:MM). Also selects the schedule year.
"""

import argparse
import json
import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from ops.update_rosters import (
    get_draft_validity,
    get_per_kook_sheet_urls,
    update_team_rosters,
    update_year_long,
)

SCHEDULE_FILE = Path(__file__).parent / "event_schedule.json"
REMINDERS_SENT_FILE = Path(__file__).parent / "reminders_sent.json"
TEAMS_FILE = Path("kook-tracker/app/rosters/teams.json")
YEAR_LONGS_FILE = Path("kook-tracker/app/rosters/year_longs.json")
TEMPLATES_DIR = Path(__file__).parent / "messages"

template_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    keep_trailing_newline=True,
)

# Coarsest to finest. On any given tick, the finest unsent reminder whose
# threshold has been crossed is the one we send.
REMINDERS = [
    ("3d", 72),
    ("1d", 24),
    ("12h", 12),
    ("1h", 1),
]
REMINDER_DISPLAY = {
    "3d": "3 days",
    "1d": "1 day",
    "12h": "12 hours",
    "1h": "1 hour",
}


def load_schedule(year: int) -> list[dict]:
    schedule = json.loads(SCHEDULE_FILE.read_text())
    return schedule.get(str(year), [])


def load_league() -> dict[str, str]:
    return json.loads(os.environ["LEAGUE_EMAILS"])


def load_reminders_sent() -> dict:
    if not REMINDERS_SENT_FILE.exists():
        return {}
    return json.loads(REMINDERS_SENT_FILE.read_text())


def save_reminders_sent(data: dict) -> None:
    REMINDERS_SENT_FILE.write_text(json.dumps(data, indent=4) + "\n")


def already_drafted(year: int, event_name: str) -> bool:
    if not TEAMS_FILE.exists():
        return False
    teams = json.loads(TEAMS_FILE.read_text())
    return event_name in teams.get(str(year), {})


def event_start_utc(event: dict) -> datetime:
    """Midnight local on the event's start date, as a UTC instant."""
    tz = ZoneInfo(event["tz"])
    d = datetime.strptime(event["start_date"], "%Y-%m-%d").date()
    return datetime(d.year, d.month, d.day, tzinfo=tz).astimezone(timezone.utc)


def hours_until(event: dict, now: datetime) -> float:
    return (event_start_utc(event) - now).total_seconds() / 3600


def build_roster_rows(rosters: dict[str, list[str]]) -> list[list[str]]:
    """Transpose {kook: [athletes...]} into rows indexed by pick number."""
    if not rosters:
        return []
    max_picks = max(len(picks) for picks in rosters.values())
    return [
        [rosters[k][i] if i < len(rosters[k]) else "" for k in rosters]
        for i in range(max_picks)
    ]


def send_summary(
    league: dict[str, str],
    event: dict,
    year: int,
    gmail_user: str,
    gmail_password: str,
) -> None:
    """Send one HTML email to the whole league with the freshly-drafted
    rosters + year-long picks for this event."""
    nickname = event.get("nickname") or event["name"]
    name = event["name"]

    teams = json.loads(TEAMS_FILE.read_text())
    rosters = teams[str(year)][name]
    if YEAR_LONGS_FILE.exists():
        year_longs = json.loads(YEAR_LONGS_FILE.read_text())
        year_long_picks = year_longs.get(str(year), {}).get(name, {})
    else:
        year_long_picks = {}

    body = template_env.get_template("summary.j2").render(
        nickname=nickname,
        kooks=list(rosters.keys()),
        roster_rows=build_roster_rows(rosters),
        year_long_picks=year_long_picks,
    )

    msg = EmailMessage()
    msg["Subject"] = f"{nickname} draft results"
    msg["From"] = gmail_user
    msg["To"] = ", ".join(f"{n} <{e}>" for n, e in league.items())
    msg.set_content(body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_password)
        smtp.send_message(msg)


def send_reminder(
    league: dict[str, str],
    per_kook_urls: dict[str, str],
    draft_validity: dict[str, bool],
    event: dict,
    tag: str,
    hours_left: float,
    gmail_user: str,
    gmail_password: str,
) -> list[str]:
    """Send an individual reminder email to each league member, reusing one
    SMTP session. Kooks with a valid draft order get reminder.j2; kooks
    whose draft has #N/A or no entries get warn.j2 with a louder subject.
    Returns the names of recipients who were emailed."""
    nickname = event.get("nickname") or event["name"]
    reminder_template = template_env.get_template("reminder.j2")
    warn_template = template_env.get_template("warn.j2")

    sent_to: list[str] = []
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_password)
        for name, email in league.items():
            url = per_kook_urls.get(name)
            if not url:
                print(f"  skipping {name}: no personal sheet in master")
                continue
            ctx = {
                "name": name,
                "nickname": nickname,
                "start_date": event["start_date"],
                "tz": event["tz"],
                "hours_left": hours_left,
                "url": url,
            }
            if draft_validity.get(name, False):
                subject = f"{nickname} draft in {REMINDER_DISPLAY[tag]}"
                body = reminder_template.render(**ctx)
            else:
                subject = (
                    f"Action needed: your {nickname} "
                    f"draft order is incomplete"
                )
                body = warn_template.render(**ctx)
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = gmail_user
            msg["To"] = f"{name} <{email}>"
            msg.set_content(body)
            smtp.send_message(msg)
            sent_to.append(name)
    return sent_to


def parse_now(s: str) -> datetime:
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"--today must be YYYY-MM-DD or YYYY-MM-DDTHH:MM, got {s!r}"
    )


def main(dry_run: bool, today: datetime | None) -> int:
    load_dotenv()
    sheet_id = os.environ.get("SHEET_ID")
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not dry_run and not all([sheet_id, gmail_user, gmail_password]):
        raise SystemExit(
            "SHEET_ID, GMAIL_USER, and GMAIL_APP_PASSWORD are all required "
            "for non-dry-run mode"
        )

    league = load_league()
    now = today or datetime.now(timezone.utc)
    year = now.year

    reminders_sent = load_reminders_sent()
    per_kook_urls: dict[str, str] | None = None  # lazy-loaded on first send
    draft_validity: dict[str, bool] | None = None
    drafted: list[str] = []
    reminded: list[tuple[str, str]] = []

    for event in load_schedule(year):
        name = event["name"]
        hrs = hours_until(event, now)

        if hrs <= 0:
            if not already_drafted(year, name):
                prefix = "[dry-run] would draft" if dry_run else "Drafting"
                print(f"{prefix} {name}")
                if not dry_run:
                    update_team_rosters(year, name, sheet_id)
                    update_year_long(
                        year, name, event.get("nickname"), sheet_id
                    )
                    send_summary(
                        league, event, year, gmail_user, gmail_password
                    )
                drafted.append(name)
            continue

        # Future event: maybe send a reminder.
        if already_drafted(year, name):
            continue

        sent = reminders_sent.setdefault(str(year), {}).setdefault(name, [])
        crossed_unsent = [
            (tag, h) for tag, h in REMINDERS if tag not in sent and hrs <= h
        ]
        if not crossed_unsent:
            continue

        # Send the finest crossed reminder; mark all crossed-but-unsent as
        # sent so a missed window doesn't backfire a stale reminder later.
        tag_to_send, _ = min(crossed_unsent, key=lambda x: x[1])
        prefix = "[dry-run] would send" if dry_run else "Sending"
        print(
            f"{prefix} {tag_to_send} reminder for {name} "
            f"({hrs:.1f}h until start)"
        )
        if not dry_run:
            if per_kook_urls is None:
                per_kook_urls = get_per_kook_sheet_urls(sheet_id)
                draft_validity = get_draft_validity(sheet_id)
            send_reminder(
                league,
                per_kook_urls,
                draft_validity,
                event,
                tag_to_send,
                hrs,
                gmail_user,
                gmail_password,
            )
        for tag, _ in crossed_unsent:
            sent.append(tag)
        reminded.append((name, tag_to_send))

    if not dry_run and reminded:
        save_reminders_sent(reminders_sent)

    if drafted:
        verb = "Would draft" if dry_run else "Drafted"
        print(f"{verb} {len(drafted)} event(s): {', '.join(drafted)}")
    if reminded:
        verb = "Would send" if dry_run else "Sent"
        print(
            f"{verb} {len(reminded)} reminder(s): "
            + ", ".join(f"{n}/{t}" for n, t in reminded)
        )
    if not drafted and not reminded:
        print("Nothing to do")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip Sheets, Resend, and file writes; print what would happen.",
    )
    parser.add_argument(
        "--today",
        type=parse_now,
        default=None,
        help="Override now (YYYY-MM-DD or YYYY-MM-DDTHH:MM, UTC).",
    )
    args = parser.parse_args()
    raise SystemExit(main(dry_run=args.dry_run, today=args.today))
