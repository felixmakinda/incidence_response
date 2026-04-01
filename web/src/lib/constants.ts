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
    color: "text-red-500",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
  },
  create_meet_link: {
    label: "Google Meet",
    color: "text-green-600",
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
  },
  create_calendar_event: {
    label: "Google Calendar",
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
  },
  create_jira_ticket: {
    label: "Jira",
    color: "text-indigo-600",
    bgColor: "bg-indigo-50",
    borderColor: "border-indigo-200",
  },
  post_slack_message: {
    label: "Slack",
    color: "text-purple-600",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
  },
  create_google_doc: {
    label: "Google Docs",
    color: "text-yellow-600",
    bgColor: "bg-yellow-50",
    borderColor: "border-yellow-200",
  },
};

export const SEVERITY_COLORS: Record<string, string> = {
  P0: "bg-red-600 text-white",
  P1: "bg-orange-500 text-white",
  P2: "bg-yellow-400 text-black",
};
