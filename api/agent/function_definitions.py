TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "gmail_reply",
            "description": (
                "Send a reply to the customer's email acknowledging the incident "
                "and stating that the engineering team is investigating urgently."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Reply subject line"},
                    "body": {"type": "string", "description": "Full reply body text"},
                    "original_message_id": {"type": "string", "description": "ID of the customer's original email"},
                },
                "required": ["to", "subject", "body", "original_message_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_meet_link",
            "description": (
                "Create a Google Meet war room link for the incident response team. "
                "IMPORTANT: Always call this BEFORE create_calendar_event — the calendar event requires the meet_url."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_title": {"type": "string", "description": "Title for the war room meeting"},
                    "incident_id": {"type": "string", "description": "Incident identifier"},
                },
                "required": ["meeting_title", "incident_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": (
                "Create a Google Calendar event for the incident war room. "
                "IMPORTANT: You MUST call create_meet_link first and pass the returned meet_url here."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "meet_url": {
                        "type": "string",
                        "description": "The Google Meet URL returned by create_meet_link — do NOT fabricate this",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses",
                    },
                    "duration_minutes": {"type": "integer", "default": 60},
                },
                "required": ["title", "meet_url", "attendees"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_jira_ticket",
            "description": "Create a P0 Jira ticket for this incident and assign it to the on-call engineer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "One-line ticket summary"},
                    "description": {"type": "string", "description": "Full incident description with context"},
                    "priority": {"type": "string", "enum": ["P0", "P1", "P2"], "default": "P0"},
                    "assignee": {
                        "type": "string",
                        "description": "On-call engineer's Jira username (denis.gathondu)",
                    },
                    "labels": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary", "description", "assignee"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "post_slack_message",
            "description": (
                "Post an incident notification to the #incidents Slack channel. "
                "IMPORTANT: Call this AFTER create_jira_ticket and create_meet_link so you can include both IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "default": "#incidents"},
                    "message": {"type": "string", "description": "Full Slack message with incident details"},
                    "jira_ticket_id": {"type": "string", "description": "Jira ticket ID from create_jira_ticket"},
                    "meet_url": {"type": "string", "description": "Meet URL from create_meet_link"},
                },
                "required": ["channel", "message", "jira_ticket_id", "meet_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_google_doc",
            "description": (
                "Create a Google Docs incident response runbook document. "
                "Call this after create_jira_ticket and create_meet_link so you can embed both IDs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "incident_summary": {"type": "string"},
                    "jira_ticket_id": {"type": "string"},
                    "meet_url": {"type": "string"},
                    "affected_service": {"type": "string"},
                    "initial_findings": {"type": "string"},
                },
                "required": ["title", "incident_summary", "jira_ticket_id", "meet_url"],
            },
        },
    },
]
