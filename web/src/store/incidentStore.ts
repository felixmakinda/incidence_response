"use client";

import { create } from "zustand";
import type {
  Incident,
  ToolCallRecord,
  AgentThought,
  StreamEvent,
  ToolCallStartData,
  ToolCallCompleteData,
  AgentThoughtData,
} from "@/types";

type AgentStatus = "idle" | "thinking" | "calling_tool" | "complete" | "failed";

interface IncidentState {
  incident: Incident | null;
  agentStatus: AgentStatus;
  activeIncidentId: string | null;
  recentIncidents: Incident[];

  setActiveIncident: (id: string) => void;
  setIncident: (incident: Incident) => void;
  setRecentIncidents: (incidents: Incident[]) => void;
  reset: () => void;
  applyStreamEvent: (event: StreamEvent) => void;
}

export const useIncidentStore = create<IncidentState>((set, _get) => ({
  incident: null,
  agentStatus: "idle",
  activeIncidentId: null,
  recentIncidents: [],

  setActiveIncident: (id) => set({ activeIncidentId: id }),

  setIncident: (incident) => set({ incident }),

  setRecentIncidents: (incidents) => set({ recentIncidents: incidents }),

  reset: () => set({ incident: null, agentStatus: "idle", activeIncidentId: null }),

  applyStreamEvent: (event: StreamEvent) => {
    switch (event.event) {
      case "incident_started": {
        set((s) => ({
          agentStatus: "thinking",
          incident: s.incident
            ? { ...s.incident, status: "running", started_at: event.timestamp }
            : null,
        }));
        break;
      }

      case "agent_thought": {
        const d = event.data as AgentThoughtData;
        const thought: AgentThought = {
          id: d.thought_id,
          content: d.content,
          timestamp: d.timestamp || event.timestamp,
          type: d.type,
        };
        set((s) => {
          if (!s.incident) return { agentStatus: "thinking" as const };
          if (s.incident.thoughts.some((t) => t.id === thought.id)) return {};
          return {
            agentStatus: "thinking" as const,
            incident: { ...s.incident, thoughts: [...s.incident.thoughts, thought] },
          };
        });
        break;
      }

      case "tool_call_start": {
        const d = event.data as ToolCallStartData;
        const record: ToolCallRecord = {
          id: d.tool_call_id,
          tool_name: d.tool_name,
          display_name: d.display_name,
          icon: d.icon,
          params: d.params,
          result: null,
          status: "running",
          started_at: event.timestamp,
          completed_at: null,
          duration_ms: null,
          depends_on: d.depends_on,
          error: null,
        };
        set((s) => {
          if (!s.incident) return {};
          const existing = s.incident.tool_calls.find((tc) => tc.id === d.tool_call_id);
          const tool_calls = existing
            ? s.incident.tool_calls.map((tc) => (tc.id === d.tool_call_id ? record : tc))
            : [...s.incident.tool_calls, record];
          return {
            agentStatus: "calling_tool",
            incident: { ...s.incident, tool_calls },
          };
        });
        break;
      }

      case "tool_call_complete": {
        const d = event.data as ToolCallCompleteData;
        set((s) => {
          if (!s.incident) return {};
          const tool_calls = s.incident.tool_calls.map((tc) =>
            tc.id === d.tool_call_id
              ? { ...tc, status: "success" as const, result: d.result, duration_ms: d.duration_ms, completed_at: event.timestamp }
              : tc
          );
          return {
            agentStatus: "thinking",
            incident: { ...s.incident, tool_calls },
          };
        });
        break;
      }

      case "tool_call_failed": {
        const d = event.data as { tool_call_id: string; tool_name: string; error: string };
        set((s) => {
          if (!s.incident) return {};
          const tool_calls = s.incident.tool_calls.map((tc) =>
            tc.id === d.tool_call_id
              ? { ...tc, status: "failed" as const, error: d.error, completed_at: event.timestamp }
              : tc
          );
          return {
            incident: { ...s.incident, tool_calls },
          };
        });
        break;
      }

      case "incident_complete": {
        set((s) => ({
          agentStatus: "complete",
          incident: s.incident
            ? { ...s.incident, status: "complete", completed_at: event.timestamp }
            : null,
        }));
        break;
      }

      case "incident_failed": {
        set((s) => ({
          agentStatus: "failed",
          incident: s.incident ? { ...s.incident, status: "failed" } : null,
        }));
        break;
      }
    }
  },
}));
