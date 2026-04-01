"""
Gmail watch() setup and renewal.
Registers a Pub/Sub push subscription so Gmail pushes a notification
to your webhook URL on every new email.

Prerequisites (one-time Google Cloud setup):
1. Create a Pub/Sub topic:
   gcloud pubsub topics create gmail-incidents

2. Grant Gmail permission to publish to it:
   gcloud pubsub topics add-iam-policy-binding gmail-incidents \
     --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" \
     --role="roles/pubsub.publisher"

3. Create a push subscription pointing at your Vercel webhook URL:
   gcloud pubsub subscriptions create gmail-incidents-push \
     --topic=gmail-incidents \
     --push-endpoint=https://YOUR_VERCEL_URL/api/gmail/webhook \
     --ack-deadline=30

4. Set GMAIL_PUBSUB_TOPIC in .env:
   GMAIL_PUBSUB_TOPIC=projects/YOUR_PROJECT_ID/topics/gmail-incidents
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from googleapiclient.discovery import build

from integrations.google_auth import get_credentials

PUBSUB_TOPIC = os.getenv("GMAIL_PUBSUB_TOPIC", "")


def _service():
    creds = get_credentials()
    if not creds:
        raise RuntimeError("Google credentials not configured.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def start_watch(label_ids: Optional[list[str]] = None) -> dict:
    """
    Register Gmail watch() for the authenticated user.
    Returns the watch response including historyId and expiration timestamp.
    Watch expires after 7 days — call renew_watch() before then.
    """
    if not PUBSUB_TOPIC:
        raise RuntimeError("GMAIL_PUBSUB_TOPIC not set in environment.")

    svc = _service()
    request_body = {
        "topicName": PUBSUB_TOPIC,
        "labelIds": label_ids or ["INBOX"],
        "labelFilterBehavior": "INCLUDE",
    }
    result = svc.users().watch(userId="me", body=request_body).execute()

    expiry_ms = int(result.get("expiration", 0))
    expiry_dt = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)

    return {
        "history_id": result.get("historyId"),
        "expiration": expiry_dt.isoformat(),
        "expires_in_days": (expiry_dt - datetime.now(tz=timezone.utc)).days,
        "topic": PUBSUB_TOPIC,
        "status": "active",
    }


def stop_watch() -> dict:
    """Stop the Gmail watch for the authenticated user."""
    svc = _service()
    svc.users().stop(userId="me").execute()
    return {"status": "stopped"}


def get_messages_since(history_id: str) -> list[dict]:
    """
    Fetch new messages since the given historyId.
    Called after receiving a Pub/Sub notification.
    """
    svc = _service()
    try:
        history = svc.users().history().list(
            userId="me",
            startHistoryId=history_id,
            historyTypes=["messageAdded"],
            labelId="INBOX",
        ).execute()
    except Exception:
        return []

    message_ids = []
    for record in history.get("history", []):
        for msg in record.get("messagesAdded", []):
            msg_id = msg["message"]["id"]
            if msg_id not in message_ids:
                message_ids.append(msg_id)

    return message_ids


def is_configured() -> bool:
    return bool(PUBSUB_TOPIC)
