"""
Background IMAP polling service.
Polls the inbox every POLL_INTERVAL_SECONDS, screens each unseen email
via LLM, and auto-triggers an incident agent if it passes the threshold.
"""

import asyncio
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from agent.screener import screen_email
from integrations.gmail_client import list_inbox_emails, mark_as_read
from models.incident import Incident, IncomingEmail, TimelineEvent

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
SCREENING_THRESHOLD = float(os.getenv("SCREENING_THRESHOLD", "0.70"))

# Tracks IMAP message IDs already processed in this server session
_processed_ids: set[str] = set()
_retries: defaultdict[str, int] = defaultdict(int)
_max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

_poller_state: dict = {
    "running": False,
    "last_checked_at": None,
    "last_triggered_at": None,
    "last_error": None,
    "emails_scanned": 0,
    "incidents_triggered": 0,
}


def get_poller_status() -> dict:
    return dict(_poller_state)


async def poll_once(event_bus, incident_store) -> None:
    """Fetch unseen emails, screen each, trigger incidents that pass."""
    emails = await asyncio.to_thread(list_inbox_emails, 20, True)
    _poller_state["emails_scanned"] += len(emails)

    for email_data in emails:
        msg_id = email_data["id"]

        # Skip already-processed messages
        if msg_id in _processed_ids or _retries[msg_id] >= _max_retries:
            continue
        if len(_processed_ids) > 2000:
            _processed_ids.clear()

        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        from_address = email_data.get("from_address", "")
        from_company = email_data.get("from_company", "")

        try:
            screening = await screen_email(
                subject=subject,
                body=body,
                from_address=from_address,
                from_company=from_company,
                confidence_threshold=SCREENING_THRESHOLD,
            )
        except Exception as e:
            _poller_state["last_error"] = f"Screener error: {e}"
            _retries[msg_id] += 1
            continue

        _processed_ids.add(msg_id)

        if not screening.get("passes_threshold"):
            continue
        # Always mark if it passes the threshold
        await asyncio.to_thread(mark_as_read, msg_id)

        # Build and store the incident
        email = IncomingEmail(
            id=msg_id,
            from_address=from_address,
            from_company=from_company,
            subject=subject,
            body=body,
            received_at=email_data.get(
                "received_at", datetime.now(tz=timezone.utc).isoformat()
            ),
        )
        incident = Incident(
            id=str(uuid.uuid4()),
            email=email,
            severity=screening.get("severity") or "P0",
            status="idle",
            timeline=[
                TimelineEvent(
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    label="Email Received (Auto)",
                    description=(
                        f"Auto-detected via IMAP polling. "
                        f"Screening confidence: {screening.get('confidence', 0):.0%}. "
                        f"{screening.get('reasoning', '')}"
                    ),
                    tool_name="email_received",
                    status="info",
                )
            ],
        )
        incident_store.create(incident)

        # Import here to avoid circular imports at module load time
        from agent.orchestrator import run_incident_agent

        asyncio.create_task(run_incident_agent(incident, event_bus))

        _poller_state["incidents_triggered"] += 1
        _poller_state["last_triggered_at"] = datetime.now(tz=timezone.utc).isoformat()


async def start_poller(event_bus, incident_store) -> None:
    """Infinite polling loop. Designed to run as a background asyncio.Task."""
    _poller_state["running"] = True
    _poller_state["last_error"] = None

    while True:
        try:
            await poll_once(event_bus, incident_store)
            _poller_state["last_checked_at"] = datetime.now(tz=timezone.utc).isoformat()
            _poller_state["last_error"] = None
        except asyncio.CancelledError:
            break
        except Exception as e:
            _poller_state["last_error"] = str(e)

        try:
            await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            break

    _poller_state["running"] = False
