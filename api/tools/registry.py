from .base import BaseTool
from .gmail import GmailReplyTool
from .google_meet import CreateMeetLinkTool
from .google_calendar import CreateCalendarEventTool
from .jira import CreateJiraTicketTool
from .slack import PostSlackMessageTool
from .google_docs import CreateGoogleDocTool

TOOL_META = {
    "gmail_reply": {"display_name": "Gmail", "icon": "gmail", "depends_on": []},
    "create_meet_link": {"display_name": "Google Meet", "icon": "meet", "depends_on": []},
    "create_calendar_event": {"display_name": "Google Calendar", "icon": "calendar", "depends_on": ["create_meet_link"]},
    "create_jira_ticket": {"display_name": "Jira", "icon": "jira", "depends_on": []},
    "post_slack_message": {"display_name": "Slack", "icon": "slack", "depends_on": ["create_jira_ticket", "create_meet_link"]},
    "create_google_doc": {"display_name": "Google Docs", "icon": "docs", "depends_on": ["create_jira_ticket", "create_meet_link"]},
}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    async def execute(self, name: str, params: dict) -> dict:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return await self._tools[name].execute(params)

    def get_meta(self, name: str) -> dict:
        return TOOL_META.get(name, {"display_name": name, "icon": "tool", "depends_on": []})


tool_registry = ToolRegistry()
tool_registry.register(GmailReplyTool())
tool_registry.register(CreateMeetLinkTool())
tool_registry.register(CreateCalendarEventTool())
tool_registry.register(CreateJiraTicketTool())
tool_registry.register(PostSlackMessageTool())
tool_registry.register(CreateGoogleDocTool())
