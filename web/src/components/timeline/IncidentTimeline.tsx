import clsx from "clsx";
import { StatusDot } from "@/components/ui/StatusDot";
import type { TimelineEvent, ToolCallRecord } from "@/types";

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

interface IncidentTimelineProps {
  timeline: TimelineEvent[];
  toolCalls: ToolCallRecord[];
}

export function IncidentTimeline({ timeline, toolCalls }: IncidentTimelineProps) {
  // Merge timeline events with tool call events chronologically
  const toolEvents: TimelineEvent[] = toolCalls
    .filter((tc) => tc.status === "success" || tc.status === "failed")
    .map((tc) => ({
      id: `tc-${tc.id}`,
      timestamp: tc.completed_at || tc.started_at || "",
      label: tc.display_name,
      description: tc.status === "success"
        ? `${tc.display_name} completed in ${tc.duration_ms}ms`
        : `${tc.display_name} failed: ${tc.error}`,
      tool_name: tc.tool_name,
      status: tc.status,
    }));

  const all = [...timeline, ...toolEvents]
    .filter((e) => e.timestamp)
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  return (
    <div>
      <h3 className="text-sm font-semibold text-zinc-700 mb-3">Timeline</h3>
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-3 top-3 bottom-3 w-0.5 bg-zinc-200" />

        <div className="space-y-3">
          {all.length === 0 && (
            <p className="text-xs text-zinc-400 italic pl-8">No events yet.</p>
          )}
          {all.map((event) => (
            <div key={event.id} className="flex items-start gap-3">
              <div className="mt-0.5 z-10">
                <StatusDot status={event.status as "pending" | "running" | "success" | "failed" | "info"} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-zinc-800">{event.label}</span>
                  <span className="text-[10px] text-zinc-400">{formatTime(event.timestamp)}</span>
                </div>
                <p className="text-xs text-zinc-500 truncate">{event.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
