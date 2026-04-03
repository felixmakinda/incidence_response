import uuid
from datetime import datetime
from .base import BaseTool
from integrations.google_auth import is_authenticated


class CreateGoogleDocTool(BaseTool):
    name = "create_google_doc"
    display_name = "Google Docs"
    depends_on = ["create_jira_ticket", "create_meet_link"]

    async def execute(self, params: dict) -> dict:
        if is_authenticated():
            return await self._real(params)
        return await self._mock(params)

    async def _real(self, params: dict) -> dict:
        import asyncio
        from integrations.google_docs_client import create_incident_doc
        result = await asyncio.to_thread(
            create_incident_doc,
            title=params["title"],
            incident_summary=params["incident_summary"],
            jira_ticket_id=params["jira_ticket_id"],
            meet_url=params["meet_url"],
            affected_service=params.get("affected_service", ""),
            initial_findings=params.get("initial_findings", ""),
        )
        return {**result, "mode": "real"}

    async def _mock(self, params: dict) -> dict:
        await self.simulate_latency(600, 1100)
        return {
            "doc_id": "new",
            "doc_url": "https://docs.new",
            "title": params.get("title"),
            "status": "created",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "mode": "mock",
        }
