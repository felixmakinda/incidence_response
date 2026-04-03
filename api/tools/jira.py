import os
import random
from .base import BaseTool
from integrations.jira_client import is_configured


class CreateJiraTicketTool(BaseTool):
    name = "create_jira_ticket"
    display_name = "Jira"
    depends_on = []

    async def execute(self, params: dict) -> dict:
        if is_configured():
            return await self._real(params)
        return await self._mock(params)

    async def _real(self, params: dict) -> dict:
        import asyncio
        from integrations.jira_client import create_ticket, get_user_account_id

        # Resolve assignee to accountId if given a username/email
        assignee = params.get("assignee", "")
        account_id = ""
        if assignee:
            account_id = await asyncio.to_thread(get_user_account_id, assignee) or ""

        result = await asyncio.to_thread(
            create_ticket,
            summary=params["summary"],
            description=params["description"],
            priority=params.get("priority", "P0"),
            assignee_account_id=account_id,
            labels=params.get("labels"),
        )
        return {**result, "mode": "real"}

    async def _mock(self, params: dict) -> dict:
        await self.simulate_latency(500, 1000)
        ticket_num = random.randint(4700, 5000)
        ticket_id = f"INC-{ticket_num}"
        jira_base = os.getenv("JIRA_BASE_URL", "").rstrip("/")
        ticket_url = f"{jira_base}/browse/{ticket_id}" if jira_base else f"INC/{ticket_id}"
        return {
            "ticket_id": ticket_id,
            "url": ticket_url,
            "summary": params.get("summary"),
            "priority": params.get("priority", "P0"),
            "assignee": params.get("assignee"),
            "status": "open",
            "project": "INC",
            "mode": "mock",
        }
