export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const TOOL_ORDER = [
  "gmail_reply",
  "create_meet_link",
  "create_calendar_event",
  "create_jira_ticket",
  "post_slack_message",
  "create_google_doc",
];

export const TOOL_DISPLAY: Record<string, { label: string; color: string; bgColor: string; borderColor: string }> = {
  gmail_reply: {
    label: "Gmail",
    color: "text-zinc-700",
    bgColor: "bg-zinc-50",
    borderColor: "border-zinc-200",
  },
  create_meet_link: {
    label: "Google Meet",
    color: "text-zinc-700",
    bgColor: "bg-zinc-50",
    borderColor: "border-zinc-200",
  },
  create_calendar_event: {
    label: "Google Calendar",
    color: "text-zinc-700",
    bgColor: "bg-zinc-50",
    borderColor: "border-zinc-200",
  },
  create_jira_ticket: {
    label: "Jira",
    color: "text-zinc-700",
    bgColor: "bg-zinc-50",
    borderColor: "border-zinc-200",
  },
  post_slack_message: {
    label: "Slack",
    color: "text-zinc-700",
    bgColor: "bg-zinc-50",
    borderColor: "border-zinc-200",
  },
  create_google_doc: {
    label: "Google Docs",
    color: "text-zinc-700",
    bgColor: "bg-zinc-50",
    borderColor: "border-zinc-200",
  },
};

export const SEVERITY_COLORS: Record<string, string> = {
  P0: "bg-red-600 text-white",
  P1: "bg-orange-500 text-white",
  P2: "bg-yellow-400 text-black",
};
