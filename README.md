# Incident Response — AI-Powered Incident Automation

An AI agent that automatically executes a full production incident response the moment a critical alert email arrives. The agent reasons step-by-step and orchestrates six external tools in the correct dependency order, streaming every decision and action live to a web dashboard.

---

## What It Does

When a P0 customer email is detected, the system:

1. **Replies to the customer** via Gmail — empathetic acknowledgement with ETA
2. **Creates a Google Meet war room** — instant video link for the response team
3. **Schedules a Google Calendar event** — war room invite sent to all attendees
4. **Files a Jira ticket** — assigned to the on-call engineer with full incident context
5. **Posts to Slack** — Block Kit alert to `#incidents` with ticket ID and Meet link
6. **Creates a Google Docs runbook** — structured incident document for the response team

All six steps happen automatically in under 60 seconds. Every tool call, agent thought, and result streams live to the dashboard.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Next.js Frontend                  │
│  Dashboard  ←── SSE Stream ──  useIncidentStream    │
│  (React + Zustand)              (EventSource)       │
└─────────────────────┬───────────────────────────────┘
                      │ REST + SSE
┌─────────────────────▼───────────────────────────────┐
│                  FastAPI Backend                     │
│                                                     │
│  POST /api/incidents/trigger                        │
│       │                                             │
│       ▼                                             │
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
└─────────────────────────────────────────────────────┘
         │           │           │           │
      Gmail       G-Meet     G-Calendar   G-Docs
       Jira        Slack
```

### Trigger Modes

| Mode | How |
|------|-----|
| **Manual** | Select a scenario email on the dashboard and click "Trigger Incident Response" |
| **Auto** | Gmail watch + Google Pub/Sub delivers real emails → LLM screener decides if it's an incident |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agent | OpenAI GPT-4o (streaming, function calling) |
| LLM Screener | GPT-4o-mini |
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
│   │   ├── gmail_client.py
│   │   ├── gmail_watch.py        # Gmail Pub/Sub watch management
│   │   ├── google_auth.py        # OAuth2 flow
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
│   │   ├── incidents.py          # POST /trigger, GET /list, GET /{id}
│   │   ├── stream.py             # GET /{id}/stream  (SSE)
│   │   ├── auth.py               # GET /auth/google (OAuth flow)
│   │   └── webhook.py            # POST /webhook/gmail (Pub/Sub receiver)
│   ├── models/                   # Pydantic data models
│   ├── services/
│   │   ├── incident_store.py     # In-memory incident state
│   │   └── event_bus.py          # SSE event publisher
│   └── mock_data/
│       └── emails.py             # Sample incident emails + on-call engineer
└── web/                          # Next.js frontend
    └── src/
        ├── app/dashboard/        # Main dashboard page
        ├── components/
        │   ├── agent/            # AgentStatusBar, AgentThoughtStream
        │   ├── email/            # EmailTriggerCard, AutoTriggerPanel
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

## Auto-Trigger: Gmail Watch

When enabled, the system monitors your Gmail inbox automatically.

```
Gmail inbox
    │  (new email arrives)
    ▼
Google Pub/Sub topic
    │  (push notification)
    ▼
Next.js /api/gmail/webhook  (public Vercel URL)
    │  (decodes + forwards)
    ▼
FastAPI POST /api/webhook/gmail
    │
    ▼
GPT-4o-mini screener
    │  confidence >= 70%?
    ├── No  → filtered, ignored
    └── Yes → incident created, agent runs
```

The screener classifies incoming email as an incident if it describes a production outage, data loss, security issue, or monitoring alert. Sales emails, support questions, and billing queries are filtered out.

---

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- `uv` — `pip install uv`
- `pnpm` — `npm install -g pnpm`
- OpenAI API key

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

Edit `api/.env`. Only `OPENAI_API_KEY` is required. Every missing credential causes that tool to fall back to mock mode.

```env
OPENAI_API_KEY=sk-...

JIRA_BASE_URL=https://yourorg.atlassian.net
JIRA_EMAIL=you@yourorg.com
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=SCRUM
JIRA_ISSUE_TYPE=Task

SLACK_BOT_TOKEN=xoxb-...

GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

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
| `http://localhost:8000/api/auth/google` | Start Google OAuth flow |

---

## Environment Variables

| Variable | Used by | Where to get it |
|----------|---------|----------------|
| `OPENAI_API_KEY` | Agent, Screener | platform.openai.com |
| `OPENAI_MODEL` | Agent | Default: `gpt-4o` |
| `SCREENER_MODEL` | Screener | Default: `gpt-4o-mini` |
| `GOOGLE_CLIENT_ID` | Gmail, Calendar, Meet, Docs | console.cloud.google.com → OAuth 2.0 |
| `GOOGLE_CLIENT_SECRET` | Gmail, Calendar, Meet, Docs | Same |
| `GOOGLE_REDIRECT_URI` | Google OAuth | Must match authorized redirect URI |
| `SLACK_BOT_TOKEN` | Slack | api.slack.com/apps → OAuth & Permissions |
| `JIRA_BASE_URL` | Jira | Your Atlassian instance URL |
| `JIRA_EMAIL` | Jira | Atlassian account email |
| `JIRA_API_TOKEN` | Jira | id.atlassian.com → Security → API tokens |
| `JIRA_PROJECT_KEY` | Jira | Project key, e.g. `INC` or `SCRUM` |
| `JIRA_ISSUE_TYPE` | Jira | Default: `Task` (use `Incident` for service desk projects) |
| `GMAIL_PUBSUB_TOPIC` | Auto-trigger | GCP Pub/Sub topic name |
| `GMAIL_PUBSUB_TOKEN` | Auto-trigger | Token for Pub/Sub push verification |
| `WEBHOOK_SECRET` | Auto-trigger | Shared secret between Next.js forwarder and FastAPI |
| `SCREENING_THRESHOLD` | Auto-trigger | Confidence cutoff 0–1 (default: `0.70`) |

---

## API Reference

### Incidents

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/incidents/trigger` | Trigger an incident from an email ID |
| `GET` | `/api/incidents/` | List recent incidents |
| `GET` | `/api/incidents/{id}` | Get a single incident with full state |
| `GET` | `/api/incidents/{id}/stream` | SSE stream for live updates |
| `GET` | `/api/emails/` | List available emails (real Gmail or mock) |

### Auth & Watch

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/auth/google` | Start Google OAuth2 flow |
| `GET` | `/api/auth/google/callback` | OAuth2 callback — set this as your redirect URI |
| `POST` | `/api/watch/start` | Start Gmail inbox watch |
| `POST` | `/api/watch/stop` | Stop Gmail inbox watch |
| `GET` | `/api/watch/status` | Watch + auth status |

### Webhooks

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/webhook/gmail` | Receive decoded email from the Next.js Pub/Sub forwarder |
| `POST` | `/api/webhook/gmail/pubsub` | Receive Pub/Sub push directly (when FastAPI is public) |

---

## Dashboard Components

| Component | What it shows |
|-----------|--------------|
| Email Trigger Card | Select a scenario and manually start the agent |
| Auto-Trigger Panel | Toggle Gmail watch; shows auth and Pub/Sub status |
| Agent Status Bar | Live agent state with SVG status icon |
| Response Pipeline | Step-by-step progress nodes with dependency arrows |
| Tool Actions | Per-tool card showing status, params, result, and duration |
| Agent Thought Stream | Real-time GPT-4o reasoning log, colour-coded by type |
| Incident Timeline | Chronological dot-and-line event list |
| Completion Overlay | Zoom-float card listing every completed action |

---

## Adding a New Integration

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide. The pattern in brief:

1. `api/integrations/your_client.py` — implement `is_configured()` and your synchronous API calls
2. `api/tools/your_tool.py` — extend `BaseTool`, implement `_real()` and `_mock()`
3. `api/tools/registry.py` — register the tool and declare its `depends_on`
4. `api/agent/function_definitions.py` — add the OpenAI function schema
5. `api/.env.example` — document the new env vars

Suggested integrations not yet built: **PagerDuty**, **Microsoft Teams**, **GitHub Issues**, **OpsGenie**.
