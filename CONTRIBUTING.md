# Contributing to Incident Response

Welcome. This document is for everyone joining the project. Read it before writing any code — it explains what the project does, how it is structured, and where contribution work is focused.

---

## What We Are Building

An AI-powered system that automatically responds to production incidents. When a critical alert email arrives, an AI agent orchestrates a full response across multiple tools:

1. Replies to the customer via **Gmail**
2. Opens a war room on **Google Meet**
3. Schedules a **Google Calendar** event with the meeting link
4. Files a ticket on **Jira**
5. Posts an alert to **Slack**
6. Creates an incident runbook on **Google Docs**

All of this happens automatically, and the progress streams live to a web dashboard.

The agent logic and dashboard are largely built. **The main focus for contributors is integrations** — connecting each tool to its real service, testing it end-to-end, and making it production-ready. There are also integration areas not yet added to the project that contributors can build from scratch.

---

## Project Structure

```
incidence_response/
├── api/                          # Python backend (FastAPI)
│   ├── agent/                    # AI orchestrator, prompt, email screener
│   ├── integrations/             # Real API clients (one file per service)
│   ├── tools/                    # Tool wrappers the agent calls
│   ├── routers/                  # REST endpoints + SSE stream
│   ├── models/                   # Pydantic data models
│   └── services/                 # Incident store + SSE event bus
└── web/                          # Next.js frontend
    └── src/
        ├── app/dashboard/        # Main incident dashboard
        ├── components/           # React components
        ├── hooks/                # SSE stream consumer
        └── store/                # Zustand state
```

### How a tool works

Every integration has two layers:

- `api/integrations/your_service_client.py` — the raw API client with an `is_configured()` check
- `api/tools/your_tool.py` — wraps the client; calls `_real()` if configured, `_mock()` if not

This means the system always runs. If credentials are missing, the tool simulates a response automatically so the rest of the agent pipeline is unaffected.

---

## Existing Integrations

These integrations exist in the codebase. Each has a working mock path and a real path that needs testing and hardening.

### Gmail
**Files:** `api/integrations/gmail_client.py`, `api/tools/gmail.py`, `api/integrations/google_auth.py`, `api/integrations/gmail_watch.py`

What it does: sends a threaded reply to the incident reporter, reads inbox emails for the dashboard, and receives Gmail push notifications via Pub/Sub.

What needs work:
- Test the full OAuth flow end-to-end (`/api/auth/google` → token saved → `is_authenticated()` returns `True`)
- Test `send_reply()` against a real Gmail account
- `mark_as_read()` exists but is never called — wire it up in the webhook handler after a successful incident trigger
- Add error handling: unauthenticated calls currently raise `RuntimeError`; return a structured error dict instead
- The Pub/Sub webhook should validate the incoming `GMAIL_PUBSUB_TOKEN` — confirm this is in place

### Google Meet
**Files:** `api/integrations/google_calendar_client.py`, `api/tools/google_meet.py`

What it does: creates a Google Meet link by inserting a short Calendar event via the Calendar API with `conferenceDataVersion=1`.

What needs work:
- Test that a real `hangoutLink` is returned after OAuth authentication
- Handle the case where the Google account does not have Meet enabled

### Google Calendar
**Files:** `api/integrations/google_calendar_client.py`, `api/tools/google_calendar.py`

What it does: creates a full calendar event with the Meet URL embedded and sends invites to all attendees.

What needs work:
- Test with real credentials; confirm attendees receive invitations
- Handle insufficient calendar write permissions gracefully (return a clear error, not a 403 crash)

### Google Docs
**Files:** `api/integrations/google_docs_client.py`, `api/tools/google_docs.py`

What it does: creates an incident runbook document in Google Drive with a structured template.

What needs work:
- Test that the document is created and accessible in Drive
- The runbook content is plain text inserted at index 1 — consider adding basic heading formatting using the Docs API `updateParagraphStyle` request

### Slack
**Files:** `api/integrations/slack_client.py`, `api/tools/slack.py`

What it does: posts a Block Kit formatted incident alert to a Slack channel with Jira and Meet links.

What needs work:
- Test with a real `SLACK_BOT_TOKEN` against a real workspace
- The Jira URL in the Block Kit message is hardcoded to `meridian.atlassian.net` — replace with the `JIRA_BASE_URL` env variable
- Add a `SLACK_INCIDENTS_CHANNEL` env variable so the channel is configurable, rather than defaulting to `#incidents` in code

### Jira
**Files:** `api/integrations/jira_client.py`, `api/tools/jira.py`

What it does: creates a Jira issue via REST API v3 (ADF format) and resolves assignee names to account IDs.

What needs work:
- Test against a real Jira project
- `"issuetype": {"name": "Incident"}` fails on projects that don't have that issue type — add a fallback to `"Bug"` or `"Task"` and document how to configure via env var
- `resp.raise_for_status()` crashes on 4xx errors — wrap in try/except and return a structured error dict
- Sanitise labels passed by the agent before sending (lowercase, replace spaces with hyphens)

---

## New Integrations to Add

These are not yet in the codebase. Contributors can pick one and build it following the pattern above.

### PagerDuty
Trigger a PagerDuty incident and assign it to the on-call engineer.
- Create `api/integrations/pagerduty_client.py` with `trigger_incident()` and `is_configured()`
- Create `api/tools/pagerduty.py` extending `BaseTool`
- Env vars to add: `PAGERDUTY_API_KEY`, `PAGERDUTY_SERVICE_ID`
- Register in `api/tools/registry.py` and add the function schema to `api/agent/function_definitions.py`

### Microsoft Teams
Post the incident alert to a Teams channel (alternative to Slack for teams using Microsoft 365).
- Create `api/integrations/teams_client.py` using an Incoming Webhook URL
- Create `api/tools/teams.py`
- Env var: `TEAMS_WEBHOOK_URL`

### GitHub Issues
Open a GitHub issue on the affected repository as part of the incident record.
- Create `api/integrations/github_client.py` using the GitHub REST API
- Create `api/tools/github.py`
- Env vars: `GITHUB_TOKEN`, `GITHUB_REPO` (format: `owner/repo`)

### OpsGenie
Create an OpsGenie alert and notify the on-call rotation.
- Create `api/integrations/opsgenie_client.py`
- Create `api/tools/opsgenie.py`
- Env vars: `OPSGENIE_API_KEY`, `OPSGENIE_TEAM`

---

## How to Add a New Integration

Follow these steps every time:

1. **Create the client** at `api/integrations/your_service_client.py`
   - Implement `is_configured() -> bool` that checks all required env vars
   - Keep API calls synchronous (use `asyncio.to_thread` in the tool layer)

2. **Create the tool** at `api/tools/your_tool.py`
   ```python
   from .base import BaseTool
   from integrations.your_service_client import is_configured

   class YourTool(BaseTool):
       name = "your_tool_name"
       display_name = "Your Service"
       depends_on = []  # list tool names this must run after

       async def execute(self, params: dict) -> dict:
           if is_configured():
               return await self._real(params)
           return await self._mock(params)

       async def _real(self, params: dict) -> dict:
           import asyncio
           from integrations.your_service_client import do_thing
           result = await asyncio.to_thread(do_thing, **params)
           return {**result, "mode": "real"}

       async def _mock(self, params: dict) -> dict:
           await self.simulate_latency(400, 900)
           return {"status": "ok", "mode": "mock"}
   ```

3. **Register the tool** in `api/tools/registry.py` — import the class, add it to `TOOL_META`, and call `tool_registry.register(YourTool())`

4. **Add the function schema** in `api/agent/function_definitions.py` so the AI agent knows when and how to call it

5. **Add env vars** to `api/.env.example` with setup instructions as comments

---

## Development Setup

```bash
# Clone
git clone git@github.com:felixmakinda/incidence_response.git
cd incidence_response

# Backend
cd api
cp .env.example .env      # fill in credentials for the integration you are working on
uv sync
uv run uvicorn main:app --reload --port 8000

# Frontend (separate terminal)
cd web
pnpm install
pnpm dev

# Or run both together from the root
npm install
npm run dev
```

API docs available at `http://localhost:8000/docs` once the backend is running.

---

## Environment Variables

| Variable | Used by | Where to get it |
|---|---|---|
| `OPENAI_API_KEY` | Agent, Screener | platform.openai.com |
| `GOOGLE_CLIENT_ID` | Gmail, Calendar, Meet, Docs | console.cloud.google.com |
| `GOOGLE_CLIENT_SECRET` | Gmail, Calendar, Meet, Docs | console.cloud.google.com |
| `SLACK_BOT_TOKEN` | Slack | api.slack.com/apps |
| `JIRA_BASE_URL` | Jira | your Atlassian instance URL |
| `JIRA_EMAIL` | Jira | your Atlassian account email |
| `JIRA_API_TOKEN` | Jira | id.atlassian.com → Security → API tokens |
| `JIRA_PROJECT_KEY` | Jira | key of your Jira project (e.g. `INC`) |

Only `OPENAI_API_KEY` is required. All other missing credentials cause that tool to fall back to mock mode automatically.

---

## Branching & Submitting Work

```bash
# Create a branch named after what you're working on
git checkout -b feat/pagerduty
git checkout -b fix/jira-error-handling
git checkout -b feat/gmail-mark-as-read

# Push and open a PR against main
git push -u origin feat/pagerduty
```

In your pull request, describe:
- What integration you worked on
- How you tested it (what credentials/accounts you used)
- Any env vars added or changed

Tag the project owner for review before merging.

---

## Questions

If you find a bug outside your area, open a GitHub issue rather than quietly fixing it. If you are unsure how something works, read the agent orchestrator at `api/agent/orchestrator.py` — it shows exactly how tools are called and how results flow between them.
