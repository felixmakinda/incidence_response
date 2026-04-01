"""Real Jira integration via REST API."""

import os
import httpx


def _base_url() -> str:
    url = os.getenv("JIRA_BASE_URL", "")
    return url.rstrip("/")


def _auth() -> tuple[str, str]:
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "")
    return email, token


def _project_key() -> str:
    return os.getenv("JIRA_PROJECT_KEY", "INC")


def is_configured() -> bool:
    return bool(os.getenv("JIRA_BASE_URL") and os.getenv("JIRA_EMAIL") and os.getenv("JIRA_API_TOKEN"))


def create_ticket(
    summary: str,
    description: str,
    priority: str = "P0",
    assignee_account_id: str = "",
    labels: list[str] | None = None,
) -> dict:
    """Create a Jira issue via the REST API."""
    base = _base_url()
    email, token = _auth()
    project = _project_key()

    # Map P0/P1/P2 to Jira priority names
    priority_map = {"P0": "Highest", "P1": "High", "P2": "Medium"}
    jira_priority = priority_map.get(priority, "Highest")

    payload: dict = {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
            "issuetype": {"name": "Incident"},
            "priority": {"name": jira_priority},
            "labels": labels or ["incident", "p0"],
        }
    }

    if assignee_account_id:
        payload["fields"]["assignee"] = {"accountId": assignee_account_id}

    resp = httpx.post(
        f"{base}/rest/api/3/issue",
        json=payload,
        auth=(email, token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    ticket_id = data.get("key", "INC-???")
    return {
        "ticket_id": ticket_id,
        "url": f"{base}/browse/{ticket_id}",
        "summary": summary,
        "priority": priority,
        "assignee": assignee_account_id or "unassigned",
        "status": "open",
        "project": project,
    }


def get_user_account_id(username_or_email: str) -> str | None:
    """Look up a Jira user's accountId by display name or email."""
    base = _base_url()
    email, token = _auth()

    resp = httpx.get(
        f"{base}/rest/api/3/user/search",
        params={"query": username_or_email},
        auth=(email, token),
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    users = resp.json()
    if users:
        return users[0].get("accountId")
    return None
