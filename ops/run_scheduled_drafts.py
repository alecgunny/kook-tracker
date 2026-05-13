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

from ops.update_rosters import update_team_rosters, update_year_long

SCHEDULE_FILE = Path(__file__).parent / "event_schedule.json"
REMINDERS_SENT_FILE = Path(__file__).parent / "reminders_sent.json"
TEAMS_FILE = Path("kook-tracker/app/rosters/teams.json")

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


def send_reminder(
    league: dict[str, str],
    event: dict,
    tag: str,
    hours_left: float,
    sheet_id: str,
    gmail_user: str,
    gmail_password: str,
) -> None:
    nickname = event.get("nickname") or event["name"]
    subject = f"{nickname} draft in {REMINDER_DISPLAY[tag]}"
    body = (
        f"The {nickname} draft will run after midnight local time on "
        f"{event['start_date']} ({event['tz']}).\n\n"
        f"That's approximately {hours_left:.1f} hours from now!\n\n"
        f"Update your draft order before then:\n"
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = ", ".join(
        f"{name} <{email}>" for name, email in league.items()
    )
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_password)
        smtp.send_message(msg)


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
            send_reminder(
                league,
                event,
                tag_to_send,
                hrs,
                sheet_id,
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
