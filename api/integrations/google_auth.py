"""
Google OAuth2 flow + credential management.

Two auth modes are supported:
  1. Service account (GOOGLE_SERVICE_ACCOUNT_JSON env var) — for server-to-server
  2. OAuth2 client (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET) — for delegated access

Tokens are persisted at GOOGLE_TOKEN_PATH (default: .google_token.json).
"""

import json
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/documents",
]

TOKEN_PATH = Path(os.getenv("GOOGLE_TOKEN_PATH", ".google_token.json"))
_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")


def _client_config() -> Optional[dict]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": [_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def get_credentials() -> Optional[Credentials]:
    """Return valid credentials or None if not configured."""
    creds: Optional[Credentials] = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_credentials(creds)
            return creds
        except Exception:
            pass

    return None


def _save_credentials(creds: Credentials):
    TOKEN_PATH.write_text(creds.to_json())


def build_authorization_url() -> Optional[str]:
    """Return the Google OAuth2 authorization URL, or None if not configured."""
    config = _client_config()
    if not config:
        return None
    flow = Flow.from_client_config(config, scopes=SCOPES, redirect_uri=_REDIRECT_URI)
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    return auth_url


def exchange_code(code: str) -> Optional[Credentials]:
    """Exchange auth code for credentials and persist them."""
    config = _client_config()
    if not config:
        return None
    flow = Flow.from_client_config(config, scopes=SCOPES, redirect_uri=_REDIRECT_URI)
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_credentials(creds)
    return creds


def is_configured() -> bool:
    return bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"))


def is_authenticated() -> bool:
    return get_credentials() is not None
