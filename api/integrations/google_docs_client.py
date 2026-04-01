"""Real Google Docs integration."""

from googleapiclient.discovery import build

from integrations.google_auth import get_credentials


def _service():
    creds = get_credentials()
    if not creds:
        raise RuntimeError("Google credentials not configured.")
    return build("docs", "v1", credentials=creds, cache_discovery=False)


def _drive_service():
    creds = get_credentials()
    if not creds:
        raise RuntimeError("Google credentials not configured.")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def create_incident_doc(
    title: str,
    incident_summary: str,
    jira_ticket_id: str,
    meet_url: str,
    affected_service: str = "",
    initial_findings: str = "",
) -> dict:
    """Create a Google Doc for the incident runbook."""
    docs_svc = _service()

    # Create the document
    doc = docs_svc.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    # Build content as a structured runbook
    content = f"""INCIDENT RESPONSE RUNBOOK
{'=' * 50}

Incident: {title}
Jira Ticket: {jira_ticket_id}
War Room: {meet_url}
Affected Service: {affected_service or 'See summary'}
Created: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

SUMMARY
-------
{incident_summary}

INITIAL FINDINGS
----------------
{initial_findings or 'Investigation in progress.'}

TIMELINE
--------
[Update this section as the incident progresses]

RESOLUTION STEPS
----------------
[Document steps taken to resolve the incident]

POST-MORTEM NOTES
-----------------
[To be filled after resolution]
"""

    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": content,
            }
        }
    ]

    docs_svc.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"

    return {
        "doc_id": doc_id,
        "doc_url": doc_url,
        "title": title,
        "status": "created",
    }
