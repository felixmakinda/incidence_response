import uuid
from .base import BaseTool
from integrations.google_auth import is_authenticated


class CreateMeetLinkTool(BaseTool):
    name = "create_meet_link"
    display_name = "Google Meet"
    depends_on = []

    async def execute(self, params: dict) -> dict:
        if is_authenticated():
            return await self._real(params)
        return await self._mock(params)

    async def _real(self, params: dict) -> dict:
        import asyncio
        from integrations.google_calendar_client import create_meet_link
        result = await asyncio.to_thread(
            create_meet_link,
            meeting_title=params.get("meeting_title", "Incident War Room"),
            incident_id=params.get("incident_id", ""),
        )
        return {**result, "mode": "real"}

    async def _mock(self, params: dict) -> dict:
        await self.simulate_latency(500, 900)
        return {
            "meet_url": "https://meet.google.com/new",
            "meeting_id": str(uuid.uuid4()),
            "status": "created",
            "title": params.get("meeting_title", "Incident War Room"),
            "mode": "mock",
        }
