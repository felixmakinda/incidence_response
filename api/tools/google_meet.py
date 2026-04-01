import uuid
import random
import string
from .base import BaseTool
from integrations.google_auth import is_authenticated


def _mock_meet_code() -> str:
    segment = lambda n: "".join(random.choices(string.ascii_lowercase, k=n))
    return f"{segment(3)}-{segment(4)}-{segment(3)}"


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
        meet_url = f"https://meet.google.com/{_mock_meet_code()}"
        return {
            "meet_url": meet_url,
            "meeting_id": str(uuid.uuid4()),
            "status": "created",
            "title": params.get("meeting_title", "Incident War Room"),
            "mode": "mock",
        }
