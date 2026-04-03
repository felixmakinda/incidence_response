import uuid
from datetime import datetime
from .base import BaseTool
from integrations.slack_client import is_configured


class PostSlackMessageTool(BaseTool):
    name = "post_slack_message"
    display_name = "Slack"
    depends_on = ["create_jira_ticket", "create_meet_link"]

    async def execute(self, params: dict) -> dict:
        if is_configured():
            return await self._real(params)
        return await self._mock(params)

    async def _real(self, params: dict) -> dict:
        import asyncio
        from integrations.slack_client import post_message
        result = await asyncio.to_thread(
            post_message,
            channel=params.get("channel", "#incidents"),
            message=params["message"],
            jira_ticket_id=params.get("jira_ticket_id", ""),
            meet_url=params.get("meet_url", ""),
        )
        return {**result, "mode": "real"}

    async def _mock(self, params: dict) -> dict:
        await self.simulate_latency(300, 700)
        ts = datetime.utcnow().timestamp()
        return {
            "message_ts": str(ts),
            "channel": params.get("channel", "#incidents"),
            "status": "posted",
            "permalink": f"https://slack.com/archives/C0INCIDENTS/p{str(ts).replace('.', '')}",
            "mode": "mock",
        }
