"""
Real Google Calendar + Google Meet integration.
Meet links are created by Calendar API with conferenceDataVersion=1.
"""

import uuid
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from integrations.google_auth import get_credentials


def _service():
    creds = get_credentials()
    if not creds:
        raise RuntimeError("Google credentials not configured.")
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def create_meet_link(meeting_title: str, incident_id: str) -> dict:
    """
    Create a Google Meet link by inserting a minimal Calendar event.
    Returns the hangoutLink for use in the real calendar event.
    """
    svc = _service()
    now = datetime.now(tz=timezone.utc)
    end = now + timedelta(hours=1)

    event = {
        "summary": meeting_title,
        "start": {"dateTime": now.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    created = svc.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1,
    ).execute()

    meet_url = created.get("hangoutLink") or ""
    return {
        "meet_url": meet_url,
        "meeting_id": created.get("id"),
        "status": "created",
        "title": meeting_title,
        "_calendar_event_id": created.get("id"),  # stored for potential deletion
    }


def create_calendar_event(
    title: str,
    meet_url: str,
    attendees: list[str],
    description: str = "",
    duration_minutes: int = 60,
) -> dict:
    """Create a full Calendar event with the Meet URL embedded."""
    svc = _service()
    now = datetime.now(tz=timezone.utc)
    end = now + timedelta(minutes=duration_minutes)

    attendee_list = [{"email": a} for a in attendees]

    # Embed Meet URL in conference data entry points
    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": now.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        "attendees": attendee_list,
        "conferenceData": {
            "conferenceSolution": {
                "name": "Google Meet",
                "key": {"type": "hangoutsMeet"},
            },
            "entryPoints": [{"entryPointType": "video", "uri": meet_url, "label": "Join War Room"}],
        },
        "sendUpdates": "all",
    }

    created = svc.events().insert(
        calendarId="primary",
        body=event,
        conferenceDataVersion=1,
        sendUpdates="all",
    ).execute()

    return {
        "event_id": created.get("id"),
        "calendar_link": created.get("htmlLink"),
        "title": title,
        "meet_url": meet_url,
        "start": created["start"].get("dateTime"),
        "end": created["end"].get("dateTime"),
        "attendees_notified": attendees,
        "status": "confirmed",
    }
