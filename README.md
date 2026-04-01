# Incident Response Automation

An AI-powered production incident response system that automatically coordinates a full response workflow when a critical alert arrives — from acknowledging the customer to creating a war room, filing a Jira ticket, notifying Slack, and generating a runbook.

---

## How It Works

When a P0/P1/P2 incident email is detected, an AI agent ("Jamie") takes over and orchestrates the following steps in sequence:

1. **Reply to the customer** via Gmail
2. **Create a Google Meet** war room link
3. **Schedule a calendar event** with the meet link
4. **Create a Jira ticket** and assign it to the on-call engineer
5. **Post to Slack** (#incidents) with the Jira link and Meet URL
6. **Generate an incident runbook** in Google Docs

All steps stream in real-time to a dashboard so your team can monitor exactly what the agent is doing and thinking.

---

## Architecture

```
incidence_response/
├── api/              # FastAPI backend (Python 3.12, uv)
│   ├── agent/        # AI orchestrator, prompt builder, email screener
│   ├── integrations/ # Gmail, Google Calendar, Docs, Meet, Slack, Jira clients
│   ├── routers/      # REST endpoints + SSE stream
│   ├── tools/        # Tool implementations (one per integration)
│   ├── models/       # Pydantic data models
│   ├── services/     # In-memory incident store + SSE event bus
│   └── mock_data/    # Test email fixtures
└── web/              # Next.js frontend (React 19, Tailwind CSS, Zustand)
    └── src/
        ├── app/dashboard/   # Main incident dashboard
        ├── components/      # Agent stream, pipeline view, timeline, email trigger
        ├── hooks/           # useIncidentStream (SSE consumer)
        └── store/           # Zustand incident state
```

---

## Tech Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Backend    | Python 3.12, FastAPI, uv                        |
| AI Agent   | OpenAI GPT-4o (agent), GPT-4o-mini (screener)  |
| Integrations | Gmail, Google Calendar, Google Meet, Google Docs, Slack, Jira |
| Real-time  | Server-Sent Events (SSE)                        |
| Frontend   | Next.js 15, React 19, Tailwind CSS v4, Zustand  |

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Node.js 18+ and [pnpm](https://pnpm.io/installation)

---

## Setup

### 1. Clone the repository

```bash
git clone git@github.com:felixmakinda/incidence_response.git
cd incidence_response
```

### 2. Configure environment variables

```bash
cp api/.env.example api/.env
```

Open `api/.env` and fill in your credentials:

```env
# Required — OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Google OAuth2 (Gmail, Calendar, Meet, Docs)
# Setup: console.cloud.google.com → APIs & Services → Credentials
# Enable: Gmail API, Google Calendar API, Google Docs API
# Add redirect URI: http://localhost:8000/api/auth/google/callback
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
GOOGLE_TOKEN_PATH=.google_token.json

# Slack — Bot User OAuth Token
# Setup: api.slack.com/apps → Bot Token Scopes: chat:write, chat:write.public
SLACK_BOT_TOKEN=xoxb-...

# Jira
# Generate API token at: id.atlassian.com/manage-profile/security/api-tokens
JIRA_BASE_URL=https://yourorg.atlassian.net
JIRA_EMAIL=you@yourorg.com
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=INC
```

> **Mock mode:** If Google, Slack, or Jira credentials are not configured, all tools fall back to simulated responses automatically. Only `OPENAI_API_KEY` is required to run the full agent flow.

### 3. Authenticate Google (optional, for real integrations)

After starting the API, visit:

```
http://localhost:8000/api/auth/google
```

Complete the OAuth flow. Your token will be saved to the path in `GOOGLE_TOKEN_PATH`.

---

## Running the Project

### Run both API and frontend together

```bash
npm install       # installs concurrently
npm run dev
```

This starts:
- API at `http://localhost:8000`
- Frontend at `http://localhost:3000`

### Run individually

```bash
# Backend
cd api
uv sync
uv run uvicorn main:app --reload --port 8000

# Frontend
cd web
pnpm install
pnpm dev
```

---

## Usage

### Via the Dashboard

1. Open `http://localhost:3000/dashboard`
2. Select a mock incident email from the **Email Trigger** panel
3. Click **Trigger Incident** to start the agent
4. Watch the agent reason and execute tools in real-time across the **Pipeline View**, **Agent Thought Stream**, and **Incident Timeline**

### Via the API

```bash
# Trigger an incident manually
curl -X POST http://localhost:8000/api/incidents/trigger \
  -H "Content-Type: application/json" \
  -d '{"severity": "P0"}'

# List all incidents
curl http://localhost:8000/api/incidents/

# Stream agent events (SSE)
curl http://localhost:8000/api/incidents/{incident_id}/stream
```

### Auto-trigger via Gmail (optional)

To have the system automatically detect and respond to production alert emails:

1. Set up a Gmail Pub/Sub watch via the API
2. Configure your Google Cloud project to publish Gmail notifications to your endpoint
3. Set `GMAIL_PUBSUB_TOPIC` and `GMAIL_PUBSUB_TOKEN` in `.env`

The email screener (GPT-4o-mini) classifies incoming emails and only triggers a response when confidence exceeds the threshold (default: 70%).

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/incidents/trigger` | Trigger a new incident response |
| `GET`  | `/api/incidents/` | List all incidents |
| `GET`  | `/api/incidents/{id}/stream` | SSE stream of agent events |
| `GET`  | `/api/emails/` | List available trigger emails |
| `POST` | `/api/webhook/gmail` | Gmail Pub/Sub webhook receiver |
| `GET`  | `/api/auth/google` | Start Google OAuth2 flow |
| `GET`  | `/api/auth/status` | Check Google auth status |

Interactive API docs are available at `http://localhost:8000/docs`.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).
