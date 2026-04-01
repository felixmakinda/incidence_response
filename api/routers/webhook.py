"""
Webhook receiver for Gmail Pub/Sub push notifications.
Also exposes watch management endpoints (start/stop/status).

Flow:
  Gmail → Pub/Sub → Next.js /api/gmail/webhook (Vercel, public URL)
       → POST /api/webhook/gmail (this FastAPI endpoint)
       → screen_email() via LLM
       → if passes → trigger incident agent
"""

import asyncio
import base64
import json
import os
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException, Header, Request

from agent.screener import screen_email
from integrations.google_auth import is_authenticated
from integrations.gmail_client import _service as gmail_service, _parse_message
from integrations.gmail_watch import start_watch, stop_watch, is_configured, get_messages_since
from models.incident import Incident, IncomingEmail, TimelineEvent
from services.event_bus import event_bus
from services.incident_store import incident_store

router = APIRouter()

# In-memory dedup set — prevents double-processing the same Gmail message
_processed_message_ids: set[str] = set()

# Store the latest historyId so we know where to resume after a notification
_last_history_id: str = ""

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
SCREENING_THRESHOLD = float(os.getenv("SCREENING_THRESHOLD", "0.70"))


@router.post("/webhook/gmail")
async def gmail_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(default=""),
):
    """
    Receives the decoded email payload forwarded by the Next.js Vercel route.
    The Next.js route handles Pub/Sub verification and Gmail message fetching;
    this endpoint handles screening and incident triggering.

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
    # Verify shared secret between Next.js route and FastAPI
    if WEBHOOK_SECRET and x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    payload = await request.json()
    message_id = payload.get("message_id", "")

    # Dedup — Pub/Sub may deliver the same notification more than once
    if message_id in _processed_message_ids:
        return {"status": "already_processed", "message_id": message_id}
    _processed_message_ids.add(message_id)
    if len(_processed_message_ids) > 1000:
        # Keep set bounded
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

    # Build the incident
    import uuid
    email = IncomingEmail(
        id=message_id,
        from_address=payload["from_address"],
        from_company=payload.get("from_company", ""),
        subject=payload["subject"],
        body=payload["body"],
        received_at=payload.get("received_at", datetime.now(tz=timezone.utc).isoformat()),
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
                description=f"Auto-triggered via Gmail watch. Screening confidence: {screening['confidence']:.0%}",
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


@router.post("/webhook/gmail/pubsub")
async def gmail_pubsub_direct(request: Request, background_tasks: BackgroundTasks):
    """
    Alternative: receive Pub/Sub push directly on FastAPI (when FastAPI is publicly hosted).
    Use this if you point the Pub/Sub push subscription at your API URL instead of Vercel.
    """
    global _last_history_id

    if not is_authenticated():
        raise HTTPException(status_code=503, detail="Google not authenticated")

    body = await request.json()

    # Verify Pub/Sub token
    pubsub_token = os.getenv("GMAIL_PUBSUB_TOKEN", "")
    token_in_query = request.query_params.get("token", "")
    if pubsub_token and token_in_query != pubsub_token:
        raise HTTPException(status_code=401, detail="Invalid Pub/Sub token")

    # Decode the Pub/Sub message
    message = body.get("message", {})
    data_b64 = message.get("data", "")
    if not data_b64:
        return {"status": "no_data"}

    try:
        data = json.loads(base64.b64decode(data_b64).decode())
    except Exception:
        return {"status": "decode_error"}

    email_address = data.get("emailAddress", "")
    history_id = str(data.get("historyId", ""))

    if not history_id:
        return {"status": "no_history_id"}

    # Fetch new message IDs since last known historyId
    start_id = _last_history_id or str(int(history_id) - 1)
    _last_history_id = history_id

    message_ids = get_messages_since(start_id)
    if not message_ids:
        return {"status": "no_new_messages"}

    # Process each new message
    results = []
    for msg_id in message_ids:
        if msg_id in _processed_message_ids:
            results.append({"message_id": msg_id, "status": "already_processed"})
            continue

        try:
            svc = gmail_service()
            raw_msg = svc.users().messages().get(userId="me", id=msg_id, format="full").execute()
            email_data = _parse_message(raw_msg)
            if not email_data:
                continue
        except Exception as e:
            results.append({"message_id": msg_id, "status": "fetch_error", "error": str(e)})
            continue

        screening = await screen_email(
            subject=email_data.get("subject", ""),
            body=email_data.get("body", ""),
            from_address=email_data.get("from_address", ""),
            from_company=email_data.get("from_company", ""),
            confidence_threshold=SCREENING_THRESHOLD,
        )

        if not screening.get("passes_threshold"):
            results.append({"message_id": msg_id, "status": "filtered", "screening": screening})
            continue

        _processed_message_ids.add(msg_id)

        import uuid
        email = IncomingEmail(
            id=msg_id,
            from_address=email_data["from_address"],
            from_company=email_data.get("from_company", ""),
            subject=email_data["subject"],
            body=email_data["body"],
            received_at=email_data.get("received_at", datetime.now(tz=timezone.utc).isoformat()),
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
                    description=f"Auto-triggered via Gmail watch. Confidence: {screening['confidence']:.0%}. {screening.get('reasoning', '')}",
                    tool_name="email_received",
                    status="info",
                )
            ],
        )
        incident_store.create(incident)
        from agent.orchestrator import run_incident_agent
        background_tasks.add_task(run_incident_agent, incident, event_bus)
        results.append({"message_id": msg_id, "status": "triggered", "incident_id": incident.id, "screening": screening})

    return {"status": "processed", "results": results}


@router.post("/watch/start")
async def start_gmail_watch():
    if not is_authenticated():
        raise HTTPException(status_code=503, detail="Google not authenticated")
    if not is_configured():
        raise HTTPException(status_code=400, detail="GMAIL_PUBSUB_TOPIC not configured")
    try:
        result = start_watch()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watch/stop")
async def stop_gmail_watch():
    if not is_authenticated():
        raise HTTPException(status_code=503, detail="Google not authenticated")
    return stop_watch()


@router.get("/watch/status")
async def watch_status():
    return {
        "google_authenticated": is_authenticated(),
        "pubsub_configured": is_configured(),
        "pubsub_topic": os.getenv("GMAIL_PUBSUB_TOPIC", ""),
        "screening_threshold": SCREENING_THRESHOLD,
        "processed_message_count": len(_processed_message_ids),
    }
