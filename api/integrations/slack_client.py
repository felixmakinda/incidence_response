"""Real Slack integration via slack_sdk."""

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def _client() -> WebClient:
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN not set.")
    return WebClient(token=token)


def is_configured() -> bool:
    return bool(os.getenv("SLACK_BOT_TOKEN"))


def post_message(channel: str, message: str, jira_ticket_id: str, meet_url: str) -> dict:
    """Post an incident notification to a Slack channel."""
    client = _client()

    # Build a rich Block Kit message
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🚨 Production Incident", "emoji": True},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": message},
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Jira Ticket:*\n<https://meridian.atlassian.net/browse/{jira_ticket_id}|{jira_ticket_id}>"},
                {"type": "mrkdwn", "text": f"*War Room:*\n<{meet_url}|Join Google Meet>"},
            ],
        },
    ]

    try:
        resp = client.chat_postMessage(
            channel=channel,
            text=message,  # fallback text
            blocks=blocks,
        )
        return {
            "message_ts": resp["ts"],
            "channel": resp["channel"],
            "status": "posted",
            "permalink": f"https://slack.com/archives/{resp['channel']}/p{resp['ts'].replace('.', '')}",
        }
    except SlackApiError as e:
        raise RuntimeError(f"Slack error: {e.response['error']}") from e
