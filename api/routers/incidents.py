import asyncio
import uuid
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from models.incident import Incident, IncomingEmail, TriggerIncidentRequest, TimelineEvent
from services.incident_store import incident_store
from services.event_bus import event_bus
from mock_data.emails import MOCK_EMAILS
from integrations.google_auth import is_authenticated

router = APIRouter()


@router.post("/incidents/trigger")
async def trigger_incident(request: TriggerIncidentRequest, background_tasks: BackgroundTasks):
    # If email_id looks like a Gmail message ID (not a mock ID), fetch it from Gmail
    if request.email_id and not request.email_id.startswith("email_") and is_authenticated():
        try:
            from integrations.gmail_client import _service, _parse_message
            svc = _service()
            msg = svc.users().messages().get(userId="me", id=request.email_id, format="full").execute()
            email_data = _parse_message(msg)
            if not email_data:
                raise HTTPException(status_code=404, detail="Could not parse Gmail message")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif request.email_id:
        email_data = next((e for e in MOCK_EMAILS if e["id"] == request.email_id), None)
        if not email_data:
            raise HTTPException(status_code=404, detail="Email not found")
    else:
        email_data = MOCK_EMAILS[0]

    email = IncomingEmail(**{k: v for k, v in email_data.items() if k in IncomingEmail.model_fields})
    incident = Incident(
        id=str(uuid.uuid4()),
        email=email,
        severity=request.severity,
        status="idle",
        timeline=[
            TimelineEvent(
                timestamp=datetime.utcnow().isoformat() + "Z",
                label="Email Received",
                description=f"Customer email received from {email.from_company}",
                tool_name="email_received",
                status="info",
            )
        ],
    )
    incident_store.create(incident)

    # Run agent in background
    from agent.orchestrator import run_incident_agent
    background_tasks.add_task(run_incident_agent, incident, event_bus)

    return {"incident_id": incident.id, "status": "started"}


@router.get("/incidents/")
async def list_incidents():
    return incident_store.list_recent()


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    incident = incident_store.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/emails/")
async def list_emails(
    source: str = Query(default="auto"),
    max_results: int = Query(default=10, le=50),
    unread_only: bool = Query(default=False),
):
    """
    Return emails for the trigger selector.
    source=auto: real Gmail if authenticated, otherwise mock
    source=mock: always return mock data
    source=gmail: force real Gmail (errors if not authenticated)
    """
    use_real = (source == "gmail") or (source == "auto" and is_authenticated())

    if use_real:
        import asyncio
        from integrations.gmail_client import list_inbox_emails
        try:
            emails = await asyncio.to_thread(list_inbox_emails, max_results, unread_only)
            return emails
        except Exception as e:
            if source == "gmail":
                raise HTTPException(status_code=503, detail=str(e))
            # Fall through to mock on auto-mode failure
    return MOCK_EMAILS
