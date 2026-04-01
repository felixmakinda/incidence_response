import uuid
from datetime import datetime, timedelta
from .base import BaseTool
from integrations.google_auth import is_authenticated


class CreateCalendarEventTool(BaseTool):
    name = "create_calendar_event"
    display_name = "Google Calendar"
    depends_on = ["create_meet_link"]

    async def execute(self, params: dict) -> dict:
        if is_authenticated():
            return await self._real(params)
        return await self._mock(params)

    async def _real(self, params: dict) -> dict:
        import asyncio
        from integrations.google_calendar_client import create_calendar_event
        result = await asyncio.to_thread(
            create_calendar_event,
            title=params["title"],
            meet_url=params["meet_url"],
            attendees=params.get("attendees", []),
            description=params.get("description", ""),
            duration_minutes=params.get("duration_minutes", 60),
        )
        return {**result, "mode": "real"}

    async def _mock(self, params: dict) -> dict:
        await self.simulate_latency(400, 900)
        now = datetime.utcnow()
        end = now + timedelta(minutes=params.get("duration_minutes", 60))
        event_id = f"event_{uuid.uuid4().hex[:10]}"
        return {
            "event_id": event_id,
            "calendar_link": f"https://calendar.google.com/event?eid={event_id}",
            "title": params.get("title"),
            "meet_url": params.get("meet_url"),
            "start": now.isoformat() + "Z",
            "end": end.isoformat() + "Z",
            "attendees_notified": params.get("attendees", []),
            "status": "confirmed",
            "mode": "mock",
        }
