"""
Gmail integration — reads inbox via IMAP and sends replies via SMTP.
Uses only Python stdlib (imaplib, smtplib).
"""

import email
import email.utils
import imaplib
import os
import re
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional


def _imap_connect() -> imaplib.IMAP4_SSL:
    host = int(os.getenv("IMAP_EMAIL_HOST"))
    port = int(os.getenv("IMAP_PORT") or "993")
    user = os.getenv("FROM_EMAIL")
    password = os.getenv("GOOGLE_APP_PASSWORD")
    if not all([host, user, password]):
        raise RuntimeError(
            "IMAP not configured: set IMAP_EMAIL_HOST, FROM_EMAIL, GOOGLE_APP_PASSWORD"
        )
    conn = imaplib.IMAP4_SSL(host, port)
    conn.login(user, password)
    return conn


def is_imap_configured() -> bool:
    return bool(
        os.getenv("IMAP_EMAIL_HOST")
        and os.getenv("FROM_EMAIL")
        and os.getenv("GOOGLE_APP_PASSWORD")
    )


def list_inbox_emails(max_results: int = 10, unread_only: bool = False) -> list[dict]:
    """Return recent inbox messages formatted for the dashboard."""
    if not is_imap_configured():
        return []

    conn = None
    try:
        conn = _imap_connect()
        conn.select("INBOX")
        search_criteria = "UNSEEN" if unread_only else "ALL"
        _, data = conn.search(None, search_criteria)
        message_nums = data[0].split()
        # IMAP returns oldest first; take the last max_results
        message_nums = message_nums[-max_results:]

        results = []
        for num in reversed(message_nums):  # newest first
            _, msg_data = conn.fetch(num, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            from_raw = msg.get("From", "")
            from_name, from_address = email.utils.parseaddr(from_raw)
            if not from_name:
                from_name = from_address

            domain = from_address.split("@")[-1] if "@" in from_address else ""
            from_company = domain.split(".")[0].title() if domain else from_name

            subject = msg.get("Subject", "(no subject)")

            # Parse received timestamp
            date_str = msg.get("Date", "")
            try:
                received_at = email.utils.parsedate_to_datetime(date_str).isoformat()
            except Exception:
                received_at = datetime.now(tz=timezone.utc).isoformat()

            # Extract body: prefer text/plain, fall back to text/html
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ct = part.get_content_type()
                    if ct == "text/plain" and not body:
                        charset = part.get_content_charset() or "utf-8"
                        body = part.get_payload(decode=True).decode(
                            charset, errors="replace"
                        )
                    elif ct == "text/html" and not body:
                        charset = part.get_content_charset() or "utf-8"
                        html = part.get_payload(decode=True).decode(
                            charset, errors="replace"
                        )
                        body = re.sub(r"<[^>]+>", "", html).strip()
            else:
                charset = msg.get_content_charset() or "utf-8"
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors="replace")
                    if msg.get_content_type() == "text/html":
                        body = re.sub(r"<[^>]+>", "", body).strip()

            results.append(
                {
                    "id": num.decode(),
                    "from_address": from_address,
                    "from_name": from_name,
                    "from_company": from_company,
                    "subject": subject,
                    "body": body[:10000],
                    "received_at": received_at,
                    "source": "imap",
                }
            )

        return results

    except Exception:
        return []
    finally:
        if conn:
            try:
                conn.logout()
            except Exception:
                pass


def send_reply(
    to_email: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
    original_message_id: Optional[str] = None,
) -> dict:
    """Send a reply email via SMTP."""
    from_email = os.getenv("FROM_EMAIL")
    password = os.getenv("GOOGLE_APP_PASSWORD")
    host = os.getenv("SMTP_EMAIL_HOST")
    port = int(os.getenv("SMTP_PORT") or os.getenv("EMAIL_PORT") or "465")

    if not all([to_email, from_email, password, host, subject, body]):
        return {
            "status": "error",
            "message": "Failed: missing one or more required parameters (to_email, from_email, password, host, subject, body)",
            "thread_id": thread_id,
            "message_id": original_message_id,
        }

    msg = MIMEText(body, "plain")
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
    domain = from_email.split("@")[-1] if "@" in from_email else ""
    msg["Message-ID"] = email.utils.make_msgid(domain=domain)
    if original_message_id:
        msg["In-Reply-To"] = original_message_id
        msg["References"] = original_message_id

    try:
        with smtplib.SMTP_SSL(host, port) as server:
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        return {
            "status": "sent",
            "message_id": msg["Message-ID"],
            "thread_id": thread_id,
            "to": to_email,
            "subject": subject,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send email: {e}",
            "thread_id": thread_id,
            "to": to_email,
            "subject": subject,
            "message_id": original_message_id,
        }


def mark_as_read(message_id: str) -> dict:
    """Mark an IMAP message as read by setting the \\Seen flag."""
    conn = None
    try:
        conn = _imap_connect()
        conn.select("INBOX")
        conn.store(message_id, "+FLAGS", "\\Seen")
        return {"status": "marked_read", "message_id": message_id}
    except Exception as e:
        return {"status": "error", "message": str(e), "message_id": message_id}
    finally:
        if conn:
            try:
                conn.logout()
            except Exception:
                pass
