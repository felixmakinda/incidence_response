"""Google OAuth2 flow endpoints."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse

from integrations.google_auth import (
    build_authorization_url,
    exchange_code,
    is_configured,
    is_authenticated,
)

router = APIRouter()


@router.get("/auth/google")
async def google_auth():
    """Start the Google OAuth2 flow."""
    if not is_configured():
        return HTMLResponse(
            "<h2>Google OAuth not configured.</h2>"
            "<p>Set <code>GOOGLE_CLIENT_ID</code> and <code>GOOGLE_CLIENT_SECRET</code> in <code>api/.env</code>.</p>",
            status_code=400,
        )
    url = build_authorization_url()
    return RedirectResponse(url=url)


@router.get("/auth/google/callback")
async def google_auth_callback(code: str):
    """Handle the OAuth2 redirect and exchange the code for tokens."""
    creds = exchange_code(code)
    if not creds:
        return HTMLResponse("<h2>Authentication failed.</h2>", status_code=400)
    return HTMLResponse(
        "<h2>Google authentication successful!</h2>"
        "<p>You can close this tab. Real Gmail, Calendar, Meet, and Docs are now active.</p>"
        "<script>window.close();</script>"
    )


@router.get("/auth/status")
async def auth_status():
    return {
        "google": {
            "configured": is_configured(),
            "authenticated": is_authenticated(),
        },
        "slack": {
            "configured": bool(__import__("os").getenv("SLACK_BOT_TOKEN")),
        },
        "jira": {
            "configured": bool(
                __import__("os").getenv("JIRA_BASE_URL")
                and __import__("os").getenv("JIRA_API_TOKEN")
            ),
        },
    }
