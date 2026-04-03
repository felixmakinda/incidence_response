# Incident Response — AI-Powered Incident Automation

An AI agent that automatically detects critical alert emails via IMAP polling, classifies them with an LLM screener, and executes a full production incident response. The agent reasons step-by-step and orchestrates six external tools in the correct dependency order, streaming every decision and action live to a web dashboard.

---

## What It Does

When a P0 customer email is detected, the system:

1. **Replies to the customer** via Gmail SMTP — empathetic acknowledgement with ETA
2. **Creates a Google Meet war room** — instant video link for the response team
3. **Schedules a Google Calendar event** — war room invite sent to all attendees
4. **Files a Jira ticket** — assigned to the on-call engineer with full incident context
5. **Posts to Slack** — Block Kit alert to `#incidents` with ticket ID and Meet link
6. **Creates a Google Docs runbook** — structured incident document for the response team

All six steps happen automatically in under 60 seconds. Every tool call, agent thought, and result streams live to the dashboard.

---

## Architecture

```
Gmail inbox  (new email arrives)
    │
    ▼
IMAP Poller  — background task, runs every 60 seconds
    │  fetches UNSEEN emails
    ▼
GPT-4o-mini screener
    │  confidence >= 70%?
    ├── No  → leave unread, skip (non-incident emails are never marked as read)
    └── Yes → mark as read, create incident, run agent
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│                  FastAPI Backend                     │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │            Agent Orchestrator               │   │
│  │  GPT-4o  ←→  Tool Definitions  ←→  Tools   │   │
│  │                                              │   │
│  │  Streaming:  agent_thought                   │   │
│  │              tool_call_start                 │   │
│  │              tool_call_complete              │   │
│  │              incident_complete               │   │
│  └──────────────┬───────────────────────────────┘   │
│                 │                                   │
│    ┌────────────▼────────────────────────┐          │
│    │           Tool Layer                │          │
│    │  gmail  meet  calendar  jira        │          │
│    │  slack  docs                        │          │
│    │  each: _real() or _mock()           │          │
│    └─────────────────────────────────────┘          │
└──────────────────────┬──────────────────────────────┘
                       │ REST + SSE
┌──────────────────────▼──────────────────────────────┐
│                   Next.js Frontend                  │
│  Dashboard  ←── SSE Stream ──  useIncidentStream    │
│  (React + Zustand)              (EventSource)       │
│                                                     │
│  Polls listIncidents() every 10s — auto-selects     │
│  newest running incident and opens SSE stream       │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agent | OpenAI GPT-4o (streaming, function calling) |
| LLM Screener | GPT-4o-mini |
| Email sending | Python `smtplib` (SMTP + App Password) |
| Email reading | Python `imaplib` (IMAP + App Password) |
| Backend | FastAPI (Python 3.12), uvicorn, SSE |
| Frontend | Next.js 15, React, Zustand, Tailwind CSS |
| Package manager (API) | uv |
| Package manager (web) | pnpm |

---

## Project Structure

```
incidence_response/
├── api/                          # Python backend (FastAPI)
│   ├── agent/
│   │   ├── orchestrator.py       # GPT-4o agent loop — streams thoughts and tool calls
│   │   ├── screener.py           # GPT-4o-mini email classifier
│   │   ├── prompt_builder.py     # System prompt + per-incident context builder
│   │   └── function_definitions.py  # OpenAI tool schemas for all six tools
│   ├── integrations/             # Raw API clients (one file per service)
│   │   ├── gmail_client.py       # IMAP inbox reader + SMTP reply sender
│   │   ├── google_auth.py        # OAuth2 flow (Calendar, Meet, Docs)
│   │   ├── google_calendar_client.py
│   │   ├── google_docs_client.py
│   │   ├── jira_client.py
│   │   └── slack_client.py
│   ├── tools/                    # Tool wrappers called by the agent
│   │   ├── base.py               # BaseTool ABC
│   │   ├── registry.py           # Registers all tools + metadata
│   │   ├── gmail.py
│   │   ├── google_meet.py
│   │   ├── google_calendar.py
│   │   ├── jira.py
│   │   ├── slack.py
│   │   └── google_docs.py
│   ├── routers/
│   │   ├── incidents.py          # GET /list, GET /{id}, GET /emails
│   │   ├── stream.py             # GET /{id}/stream  (SSE)
│   │   ├── auth.py               # GET /auth/google (OAuth flow)
│   │   └── webhook.py            # POST /webhook/gmail, GET /watch/status
│   ├── models/                   # Pydantic data models
│   ├── services/
│   │   ├── incident_store.py     # In-memory incident state
│   │   ├── event_bus.py          # SSE event publisher
│   │   └── inbox_poller.py       # Background IMAP polling loop
│   └── mock_data/
│       └── emails.py             # Sample incident emails + on-call engineer
└── web/                          # Next.js frontend
    └── src/
        ├── app/dashboard/        # Main dashboard page
        ├── components/
        │   ├── agent/            # AgentStatusBar, AgentThoughtStream
        │   ├── email/            # AutoTriggerPanel (IMAP/SMTP status)
        │   ├── pipeline/         # PipelineView (step progress bar)
        │   ├── timeline/         # IncidentTimeline
        │   ├── tools/            # ToolCard, ToolStatusBadge
        │   └── ui/               # Badge, Spinner, StatusDot, IncidentCompleteOverlay
        ├── hooks/
        │   └── useIncidentStream.ts  # EventSource SSE consumer
        ├── store/
        │   └── incidentStore.ts  # Zustand store, applies SSE events to state
        └── lib/
            ├── api.ts            # fetch wrappers for backend REST endpoints
            └── constants.ts      # tool display metadata, ordering
```

---

## How the Agent Works

### Automatic Trigger Flow

1. `inbox_poller.py` runs as a background `asyncio.Task` from server startup
2. Every 60 seconds it fetches UNSEEN emails via IMAP
3. Each email is sent to GPT-4o-mini for incident classification
4. Emails that pass the confidence threshold (default 70%) create an `Incident` and start the agent
5. Confirmed incident emails are marked as read; non-incidents are left untouched in Gmail
6. The dashboard polls `listIncidents()` every 10 seconds and auto-connects the SSE stream when a new running incident appears

### Agent Loop (`api/agent/orchestrator.py`)

1. Builds a message history starting with the system prompt and the incident email
2. Calls GPT-4o with streaming enabled and the six tool schemas attached
3. Streams the model's reasoning — each sentence is classified and emitted as an `agent_thought` SSE event
4. When the model emits tool calls, each is executed sequentially by the tool registry
5. Results are appended back to the message history as `role: tool` messages
6. The loop repeats until the model responds with no tool calls (done) or 12 iterations are reached

### Thought Classification

Agent thoughts are classified into three types as they stream:

| Type | Trigger words |
|------|--------------|
| `decision` | must, should, will, going to, next, then |
| `observation` | noticed, see, result, returned, completed |
| `reasoning` | everything else |

### Tool Dependency Ordering

The agent enforces ordering through its system prompt. Dependencies are also declared in `registry.py`:

```
gmail_reply            (no deps)
create_meet_link       (no deps)
create_calendar_event  ← needs meet_url from create_meet_link
create_jira_ticket     (no deps)
post_slack_message     ← needs jira_ticket_id + meet_url
create_google_doc      ← needs jira_ticket_id + meet_url
```

---

## How the Tool Layer Works

Every integration has two layers:

```python
# integrations/your_service_client.py — raw synchronous API client
def is_configured() -> bool:
    return bool(os.getenv("YOUR_API_KEY"))

def do_thing(param: str) -> dict: ...

# tools/your_tool.py — async wrapper called by the agent
class YourTool(BaseTool):
    async def execute(self, params: dict) -> dict:
        if is_configured():
            return await self._real(params)   # hits the real API
        return await self._mock(params)        # returns simulated data
```

If credentials are missing, the tool silently falls back to mock mode. The rest of the pipeline is unaffected.

---

## Real-time Streaming

The backend publishes SSE events as the agent runs. The frontend consumes them via `EventSource`.

### Event Types

| Event | When |
|-------|------|
| `incident_started` | Agent loop begins |
| `agent_thought` | Each reasoning sentence from GPT-4o |
| `tool_call_start` | Before a tool executes |
| `tool_call_complete` | After successful tool execution |
| `tool_call_failed` | After a tool error |
| `incident_complete` | Agent loop ends, all tools done |
| `incident_failed` | Unrecoverable error |

### Frontend State

The Zustand store (`incidentStore.ts`) receives each event and updates:

- `agentStatus` — `idle | thinking | calling_tool | complete | failed`
- `incident.tool_calls` — live status, params, result, and duration per tool
- `incident.thoughts` — agent reasoning log
- `incident.timeline` — chronological event list

On completion, the dashboard fires a 5-second confetti fireworks animation and a zoom-float overlay card listing every action taken.

---

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- `uv` — `pip install uv`
- `pnpm` — `npm install -g pnpm`
- OpenAI API key
- A Gmail account with [App Passwords](https://myaccount.google.com/apppasswords) enabled (requires 2FA)

### 1 — Clone and install

```bash
git clone git@github.com:felixmakinda/incidence_response.git
cd incidence_response

# Backend
cd api && cp .env.example .env && uv sync

# Frontend
cd ../web && pnpm install
```

### 2 — Configure environment

Edit `api/.env`. The minimum required to run with real email detection:

```env
# Required — AI brain
OPENAI_API_KEY=sk-...

# Required — inbox polling and customer reply
FROM_EMAIL=your-email@gmail.com
GOOGLE_APP_PASSWORD=your-app-password
SMTP_EMAIL_HOST=smtp.gmail.com
SMTP_PORT=465
IMAP_EMAIL_HOST=imap.gmail.com
IMAP_PORT=993
```

Every other credential (Jira, Slack, Google OAuth) is optional — missing ones fall back to mock mode.

### 3 — Run

```bash
# Both services from the repo root
npm install && npm run dev

# Or separately
cd api  && uv run uvicorn main:app --reload --port 8000
cd web  && pnpm dev
```

| URL | What |
|-----|------|
| `http://localhost:3000` | Dashboard |
| `http://localhost:8000/docs` | FastAPI interactive API docs |
| `http://localhost:8000/api/auth/google` | Start Google OAuth flow (Calendar/Meet/Docs) |

### 4 — Verify the poller is running

Open the dashboard. The **Auto-Trigger** panel shows three status chips:

- **IMAP** — green when `IMAP_EMAIL_HOST`, `FROM_EMAIL`, and `GOOGLE_APP_PASSWORD` are set
- **SMTP** — green when `SMTP_EMAIL_HOST`, `FROM_EMAIL`, and `GOOGLE_APP_PASSWORD` are set
- **Poller** — green when the background polling loop is active

Once IMAP is green, send a test incident email to your inbox. The dashboard will automatically show the incident within 60 seconds.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key |
| `OPENAI_MODEL` | | `gpt-4o` | Model for the agent |
| `OPENAI_BASE_URL` | | — | Override for OpenAI-compatible APIs |
| `SCREENER_MODEL` | | `gpt-4o-mini` | Model for email classification |
| `FROM_EMAIL` | ✅ | — | Gmail address used for IMAP and SMTP |
| `GOOGLE_APP_PASSWORD` | ✅ | — | Gmail App Password (not your account password) |
| `SMTP_EMAIL_HOST` | | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | | `465` | SMTP SSL port |
| `IMAP_EMAIL_HOST` | | `imap.gmail.com` | IMAP server hostname |
| `IMAP_PORT` | | `993` | IMAP SSL port |
| `POLL_INTERVAL_SECONDS` | | `60` | How often the poller checks for new emails |
| `SCREENING_THRESHOLD` | | `0.70` | Minimum LLM confidence to trigger an incident |
| `MAX_RETRIES` | | `3` | Max screener retries per email before giving up |
| `WEBHOOK_SECRET` | | — | Shared secret for `POST /api/webhook/gmail` |
| `SLACK_BOT_TOKEN` | | — | Slack Bot User OAuth Token |
| `JIRA_BASE_URL` | | — | Atlassian instance URL |
| `JIRA_EMAIL` | | — | Atlassian account email |
| `JIRA_API_TOKEN` | | — | Atlassian API token |
| `JIRA_PROJECT_KEY` | | `INC` | Jira project key |
| `JIRA_ISSUE_TYPE` | | `Task` | `Task`/`Bug` for Scrum, `Incident` for service desk |
| `GOOGLE_CLIENT_ID` | | — | Google OAuth client ID (Calendar/Meet/Docs) |
| `GOOGLE_CLIENT_SECRET` | | — | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | | `http://localhost:8000/api/auth/google/callback` | OAuth redirect URI |
| `GOOGLE_TOKEN_PATH` | | `.google_token.json` | Where OAuth token is persisted |

---

## API Reference

### Incidents

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/incidents/` | List recent incidents |
| `GET` | `/api/incidents/{id}` | Get a single incident with full state |
| `GET` | `/api/incidents/{id}/stream` | SSE stream for live updates |
| `GET` | `/api/emails/` | List available emails (real IMAP or mock) |

### Auth & Status

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/auth/google` | Start Google OAuth2 flow (Calendar/Meet/Docs) |
| `GET` | `/api/auth/google/callback` | OAuth2 callback — set this as your redirect URI |
| `GET` | `/api/watch/status` | IMAP/SMTP config + live poller state |

### Webhooks

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/webhook/gmail` | Receive a decoded email payload and screen + trigger it |

---

## Dashboard

| Component | What it shows |
|-----------|--------------|
| Auto-Trigger Panel | IMAP/SMTP config status, poller running state, last-checked time, email/incident counters |
| Agent Status Bar | Live agent state with SVG status icon |
| Response Pipeline | Step-by-step progress nodes with dependency arrows |
| Tool Actions | Per-tool card showing status, params, result, and duration |
| Agent Thought Stream | Real-time GPT-4o reasoning log, colour-coded by type |
| Incident Timeline | Chronological dot-and-line event list |
| Completion Overlay | Zoom-float card listing every completed action |

The dashboard polls for new incidents every 10 seconds and automatically opens the SSE stream for the newest running incident. Clicking an older incident in the sidebar switches the live view to that incident.

---

## Adding a New Integration

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. The pattern in brief:

1. `api/integrations/your_client.py` — implement `is_configured()` and your synchronous API calls
2. `api/tools/your_tool.py` — extend `BaseTool`, implement `_real()` and `_mock()`
3. `api/tools/registry.py` — register the tool and declare its `depends_on`
4. `api/agent/function_definitions.py` — add the OpenAI function schema
5. `api/.env.example` — document the new env vars

Suggested integrations not yet built: **PagerDuty**, **Microsoft Teams**, **GitHub Issues**, **OpsGenie**.
