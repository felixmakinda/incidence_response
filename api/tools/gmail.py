import uuid
from datetime import datetime
from .base import BaseTool
from integrations.google_auth import is_authenticated


class GmailReplyTool(BaseTool):
    name = "gmail_reply"
    display_name = "Gmail"
    depends_on = []

    async def execute(self, params: dict) -> dict:
        if is_authenticated():
            return await self._real(params)
        return await self._mock(params)

    async def _real(self, params: dict) -> dict:
        import asyncio
        from integrations.gmail_client import send_reply
        result = await asyncio.to_thread(
            send_reply,
            to=params["to"],
            subject=params.get("subject", ""),
            body=params["body"],
            thread_id=params.get("thread_id"),
            original_message_id=params.get("original_message_id"),
        )
        return {**result, "mode": "real"}

    async def _mock(self, params: dict) -> dict:
        await self.simulate_latency(400, 800)
        return {
            "message_id": f"msg_{uuid.uuid4().hex[:12]}",
            "thread_id": f"thread_{uuid.uuid4().hex[:10]}",
            "status": "sent",
            "to": params.get("to"),
            "subject": params.get("subject"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mode": "mock",
        }
