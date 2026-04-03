import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from .base import BaseTool
from integrations.google_auth import is_authenticated


def _calendar_template_url(title: str, start: datetime, end: datetime, description: str, meet_url: str) -> str:
    fmt = "%Y%m%dT%H%M%SZ"
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start.strftime(fmt)}/{end.strftime(fmt)}",
        "details": description or f"War Room: {meet_url}",
        "location": meet_url,
    }
    return f"https://calendar.google.com/calendar/render?{urlencode(params)}"


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
        now = datetime.now(tz=timezone.utc)
        end = now + timedelta(minutes=params.get("duration_minutes", 60))
        title = params.get("title", "Incident War Room")
        meet_url = params.get("meet_url", "")
        description = params.get("description", "")
        calendar_link = _calendar_template_url(title, now, end, description, meet_url)
        return {
            "event_id": f"event_{uuid.uuid4().hex[:10]}",
            "calendar_link": calendar_link,
            "title": title,
            "meet_url": meet_url,
            "start": now.isoformat(),
            "end": end.isoformat(),
            "attendees_notified": params.get("attendees", []),
            "status": "confirmed",
            "mode": "mock",
        }
