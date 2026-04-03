import asyncio

from integrations.gmail_client import list_inbox_emails, send_reply

from .base import BaseTool


class GmailReplyTool(BaseTool):
    name = "gmail_reply"
    display_name = "Gmail Reply"
    depends_on = []

    async def execute(self, params: dict) -> dict:
        result = await asyncio.to_thread(
            send_reply,
            to_email=params["to"],
            subject=params.get("subject", ""),
            body=params["body"],
            thread_id=params.get("thread_id"),
            original_message_id=params.get("original_message_id"),
        )
        return result


class GmailInboxTool(BaseTool):
    name = "gmail_inbox"
    display_name = "Gmail Inbox"
    depends_on = []

    async def execute(self, params: dict) -> dict:
        max_results = params.get("max_results", 10)
        unread_only = params.get("unread_only", False)
        emails = await asyncio.to_thread(list_inbox_emails, max_results, unread_only)
        return {"emails": emails, "count": len(emails), "status": "success"}
