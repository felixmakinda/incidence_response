"""
Real Gmail integration — reads inbox emails and sends replies.
Falls back gracefully if not authenticated.
"""

import base64
import email as email_lib
import os
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional

from googleapiclient.discovery import build

from integrations.google_auth import get_credentials


def _service():
    creds = get_credentials()
    if not creds:
        raise RuntimeError("Google credentials not configured. Visit /api/auth/google to authenticate.")
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_inbox_emails(max_results: int = 10, unread_only: bool = False) -> list[dict]:
    """Return recent inbox messages formatted for the dashboard."""
    svc = _service()
    query = "in:inbox"
    if unread_only:
        query += " is:unread"

    result = svc.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    emails = []
    for msg in messages:
        detail = svc.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        parsed = _parse_message(detail)
        if parsed:
            emails.append(parsed)
    return emails


def _parse_message(msg: dict) -> Optional[dict]:
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    from_raw = headers.get("from", "")
    subject = headers.get("subject", "(no subject)")
    date_str = headers.get("date", "")

    # Extract name and email from "Name <email>" format
    if "<" in from_raw:
        from_name = from_raw.split("<")[0].strip().strip('"')
        from_address = from_raw.split("<")[1].rstrip(">").strip()
    else:
        from_name = from_raw
        from_address = from_raw

    # Parse company from email domain (simple heuristic)
    domain = from_address.split("@")[-1] if "@" in from_address else ""
    company = domain.split(".")[0].title() if domain else from_name

    body = _extract_body(msg.get("payload", {}))

    # Parse received timestamp
    try:
        internal_date = int(msg.get("internalDate", 0)) / 1000
        received_at = datetime.fromtimestamp(internal_date, tz=timezone.utc).isoformat()
    except Exception:
        received_at = datetime.now(tz=timezone.utc).isoformat()

    return {
        "id": msg["id"],
        "from_address": from_address,
        "from_name": from_name,
        "from_company": company,
        "subject": subject,
        "body": body,
        "received_at": received_at,
        "thread_id": msg.get("threadId"),
        "source": "gmail",
    }


def _extract_body(payload: dict) -> str:
    """Recursively extract plain-text body from MIME payload."""
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if body_data:
        decoded = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
        if mime_type == "text/plain":
            return decoded
        if mime_type == "text/html":
            # Strip basic HTML tags
            import re
            return re.sub(r"<[^>]+>", "", decoded).strip()

    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return ""


def send_reply(
    to: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    original_message_id: Optional[str] = None,
) -> dict:
    """Send a reply email via Gmail API."""
    svc = _service()

    mime = MIMEText(body, "plain")
    mime["to"] = to
    mime["subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
    if original_message_id:
        mime["In-Reply-To"] = original_message_id
        mime["References"] = original_message_id

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    body_payload: dict = {"raw": raw}
    if thread_id:
        body_payload["threadId"] = thread_id

    sent = svc.users().messages().send(userId="me", body=body_payload).execute()
    return {
        "message_id": sent.get("id"),
        "thread_id": sent.get("threadId"),
        "status": "sent",
        "to": to,
        "subject": mime["subject"],
    }


def mark_as_read(message_id: str):
    svc = _service()
    svc.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()
