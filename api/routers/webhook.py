"""
Webhook receiver for email payloads forwarded from external sources.
Also exposes a status endpoint for IMAP/SMTP configuration.

Flow (manual trigger):
  External email payload → POST /api/webhook/gmail (this FastAPI endpoint)
  → screen_email() via LLM
  → if passes → trigger incident agent
"""

import os
import uuid
from datetime import datetime, timezone

from agent.screener import screen_email
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from models.incident import Incident, IncomingEmail, TimelineEvent
from services.event_bus import event_bus
from services.incident_store import incident_store

router = APIRouter()

# In-memory dedup set — prevents double-processing the same email message
_processed_message_ids: set[str] = set()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
SCREENING_THRESHOLD = float(os.getenv("SCREENING_THRESHOLD", "0.70"))


@router.post("/webhook/gmail")
async def gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(default=""),
):
    """
    Receives a decoded email payload and triggers incident screening + agent.

    Expected body:
    {
      "message_id": str,
      "from_address": str,
      "from_company": str,
      "subject": str,
      "body": str,
      "received_at": str,
      "thread_id": str | null
    }
    """
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    payload = await request.json()
    message_id = payload.get("message_id", "")

    # Dedup — prevent double-processing
    if message_id in _processed_message_ids:
        return {"status": "already_processed", "message_id": message_id}
    _processed_message_ids.add(message_id)
    if len(_processed_message_ids) > 1000:
        _processed_message_ids.clear()

    # Run LLM screening
    screening = await screen_email(
        subject=payload.get("subject", ""),
        body=payload.get("body", ""),
        from_address=payload.get("from_address", ""),
        from_company=payload.get("from_company", ""),
        confidence_threshold=SCREENING_THRESHOLD,
    )

    if not screening.get("passes_threshold"):
        return {
            "status": "filtered",
            "message_id": message_id,
            "screening": screening,
        }

    email = IncomingEmail(
        id=message_id,
        from_address=payload["from_address"],
        from_company=payload.get("from_company", ""),
        subject=payload["subject"],
        body=payload["body"],
        received_at=payload.get(
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
                description=f"Auto-triggered via webhook. Screening confidence: {screening['confidence']:.0%}",
                tool_name="email_received",
                status="info",
            )
        ],
    )
    incident_store.create(incident)

    from agent.orchestrator import run_incident_agent

    background_tasks.add_task(run_incident_agent, incident, event_bus)

    return {
        "status": "triggered",
        "incident_id": incident.id,
        "message_id": message_id,
        "screening": screening,
    }


@router.get("/watch/status")
async def watch_status():
    from services.inbox_poller import get_poller_status

    return {
        "imap_configured": bool(
            os.getenv("IMAP_EMAIL_HOST")
            and os.getenv("FROM_EMAIL")
            and os.getenv("GOOGLE_APP_PASSWORD")
        ),
        "smtp_configured": bool(
            os.getenv("SMTP_EMAIL_HOST")
            and os.getenv("FROM_EMAIL")
            and os.getenv("GOOGLE_APP_PASSWORD")
        ),
        "imap_host": os.getenv("IMAP_EMAIL_HOST", ""),
        "screening_threshold": SCREENING_THRESHOLD,
        "processed_message_count": len(_processed_message_ids),
        "poller": get_poller_status(),
    }
