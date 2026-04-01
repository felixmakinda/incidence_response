"use client";

import { useEffect, useState } from "react";
import { EmailTriggerCard } from "@/components/email/EmailTriggerCard";
import { AutoTriggerPanel } from "@/components/email/AutoTriggerPanel";
import { AgentStatusBar } from "@/components/agent/AgentStatusBar";
import { PipelineView } from "@/components/pipeline/PipelineView";
import { ToolCard } from "@/components/tools/ToolCard";
import { AgentThoughtStream } from "@/components/agent/AgentThoughtStream";
import { IncidentTimeline } from "@/components/timeline/IncidentTimeline";
import { useIncidentStore } from "@/store/incidentStore";
import { useIncidentStream } from "@/hooks/useIncidentStream";
import { listEmails, listIncidents } from "@/lib/api";
import { SEVERITY_COLORS } from "@/lib/constants";
import clsx from "clsx";
import type { MockEmail } from "@/types";

export default function DashboardPage() {
  const [emails, setEmails] = useState<MockEmail[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  const { incident, agentStatus, setRecentIncidents } = useIncidentStore();

  // Load emails and recent incidents on mount
  useEffect(() => {
    listEmails().then(setEmails);
    listIncidents().then(setRecentIncidents);
  }, [setRecentIncidents]);

  // Subscribe to SSE stream for active incident
  useIncidentStream(activeId);

  function handleIncidentStarted(id: string) {
    setActiveId(id);
    // Refresh sidebar list
    listIncidents().then(setRecentIncidents);
  }

  return (
    <div className="flex flex-col h-full gap-4 p-5 overflow-y-auto">
      {/* Top row: email trigger + auto-trigger + status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 flex flex-col gap-3">
          <EmailTriggerCard emails={emails} onIncidentStarted={handleIncidentStarted} />
          <AutoTriggerPanel />
        </div>
        <div className="flex flex-col gap-3">
          <AgentStatusBar status={agentStatus} />
          {incident && (
            <div className="bg-white rounded-xl border border-zinc-200 px-4 py-3 space-y-1">
              <div className="flex items-center gap-2">
                <span className={clsx("text-xs font-bold px-2 py-1 rounded", SEVERITY_COLORS[incident.severity])}>
                  {incident.severity}
                </span>
                <span className="text-xs text-zinc-600 font-medium truncate">{incident.email.from_company}</span>
              </div>
              <p className="text-xs text-zinc-500 truncate">{incident.email.subject}</p>
              <div className="flex items-center gap-3 text-xs text-zinc-400">
                <span>Tools: {incident.tool_calls.filter((t) => t.status === "success").length}/6</span>
                {incident.started_at && (
                  <ElapsedTimer startedAt={incident.started_at} status={incident.status} />
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Pipeline view */}
      {incident && (
        <div className="bg-white rounded-xl border border-zinc-200 shadow-sm px-5 py-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-zinc-800">Response Pipeline</h2>
            <span className="text-xs text-zinc-400">Execution order enforced by agent</span>
          </div>
          <PipelineView toolCalls={incident.tool_calls} />
        </div>
      )}

      {/* Main content: tool cards + thought stream */}
      {incident && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 flex-1">
          {/* Tool cards grid */}
          <div className="lg:col-span-3 space-y-3">
            <h2 className="text-sm font-semibold text-zinc-800">Tool Actions</h2>
            {incident.tool_calls.length === 0 && (
              <p className="text-xs text-zinc-400 italic">Agent has not executed any tools yet.</p>
            )}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              {incident.tool_calls.map((tc) => (
                <ToolCard key={tc.id} toolCall={tc} />
              ))}
            </div>
          </div>

          {/* Thought stream */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-zinc-200 shadow-sm p-4 flex flex-col min-h-64 max-h-125">
            <AgentThoughtStream thoughts={incident.thoughts} agentStatus={agentStatus} />
          </div>
        </div>
      )}

      {/* Timeline */}
      {incident && (
        <div className="bg-white rounded-xl border border-zinc-200 shadow-sm px-5 py-4">
          <IncidentTimeline timeline={incident.timeline} toolCalls={incident.tool_calls} />
        </div>
      )}

      {!incident && emails.length > 0 && (
        <div className="flex-1 flex items-center justify-center text-zinc-400">
          <div className="text-center">
            <p className="text-4xl mb-3">🚨</p>
            <p className="text-base font-medium text-zinc-600">No active incident</p>
            <p className="text-sm text-zinc-400">Select an email above and click "Trigger Incident Response"</p>
          </div>
        </div>
      )}
    </div>
  );
}

function ElapsedTimer({ startedAt, status }: { startedAt: string; status: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (status === "complete" || status === "failed") return;
    const start = new Date(startedAt).getTime();
    const id = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [startedAt, status]);

  const final = status === "complete" || status === "failed"
    ? Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)
    : elapsed;

  return <span>{final}s elapsed</span>;
}
