export type IncidentSeverity = "P0" | "P1" | "P2";
export type IncidentStatus = "idle" | "running" | "complete" | "failed";
export type ToolStatus = "pending" | "running" | "success" | "failed";
export type ThoughtType = "reasoning" | "decision" | "observation";

export type ToolName =
  | "gmail_reply"
  | "create_meet_link"
  | "create_calendar_event"
  | "create_jira_ticket"
  | "post_slack_message"
  | "create_google_doc";

export interface IncomingEmail {
  id: string;
  from_address: string;
  from_company: string;
  subject: string;
  body: string;
  received_at: string;
}

export interface ToolCallRecord {
  id: string;
  tool_name: string;
  display_name: string;
  icon: string;
  params: Record<string, unknown>;
  result: Record<string, unknown> | null;
  status: ToolStatus;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  depends_on: string[];
  error: string | null;
}

export interface AgentThought {
  id: string;
  content: string;
  timestamp: string;
  type: ThoughtType;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  label: string;
  description: string;
  tool_name: string;
  status: string;
}

export interface Incident {
  id: string;
  email: IncomingEmail;
  severity: IncidentSeverity;
  status: IncidentStatus;
  started_at: string | null;
  completed_at: string | null;
  tool_calls: ToolCallRecord[];
  thoughts: AgentThought[];
  timeline: TimelineEvent[];
}

export type StreamEventType =
  | "incident_started"
  | "agent_thought"
  | "tool_call_start"
  | "tool_call_complete"
  | "tool_call_failed"
  | "incident_complete"
  | "incident_failed";

export interface StreamEvent<T = unknown> {
  event: StreamEventType;
  incident_id: string;
  timestamp: string;
  data: T;
}

export interface ToolCallStartData {
  tool_call_id: string;
  tool_name: string;
  display_name: string;
  icon: string;
  params: Record<string, unknown>;
  depends_on: string[];
}

export interface ToolCallCompleteData {
  tool_call_id: string;
  tool_name: string;
  result: Record<string, unknown>;
  duration_ms: number;
}

export interface AgentThoughtData {
  thought_id: string;
  content: string;
  type: ThoughtType;
  timestamp: string;
}

export interface MockEmail {
  id: string;
  from_address: string;
  from_company: string;
  subject: string;
  body: string;
}
