from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from services.event_bus import event_bus
from services.incident_store import incident_store

router = APIRouter()


@router.get("/incidents/{incident_id}/stream")
async def stream_incident(incident_id: str):
    if not incident_store.get(incident_id):
        raise HTTPException(status_code=404, detail="Incident not found")

    return StreamingResponse(
        event_bus.stream(incident_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
