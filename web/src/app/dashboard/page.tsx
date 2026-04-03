"use client";

import { useEffect, useState } from "react";
import confetti from "canvas-confetti";
import { EmailTriggerCard } from "@/components/email/EmailTriggerCard";
import { AutoTriggerPanel } from "@/components/email/AutoTriggerPanel";
import { AgentStatusBar } from "@/components/agent/AgentStatusBar";
import { PipelineView } from "@/components/pipeline/PipelineView";
import { ToolCard } from "@/components/tools/ToolCard";
import { AgentThoughtStream } from "@/components/agent/AgentThoughtStream";
import { IncidentTimeline } from "@/components/timeline/IncidentTimeline";
import { IncidentCompleteOverlay } from "@/components/ui/IncidentCompleteOverlay";
import { useIncidentStore } from "@/store/incidentStore";
import { useIncidentStream } from "@/hooks/useIncidentStream";
import { getIncident, listEmails, listIncidents } from "@/lib/api";
import type { MockEmail } from "@/types";
import { SEVERITY_COLORS } from "@/lib/constants";
import clsx from "clsx";

export default function DashboardPage() {
  const [emails, setEmails] = useState<MockEmail[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  const {
    incident,
    agentStatus,
    recentIncidents,
    activeIncidentId,
    setIncident,
    setRecentIncidents,
  } = useIncidentStore();

  // Load emails on mount and poll for new incidents every 10 seconds
  useEffect(() => {
    listEmails().then(setEmails);
    listIncidents().then(setRecentIncidents);
    const id = setInterval(() => listIncidents().then(setRecentIncidents), 10_000);
    return () => clearInterval(id);
  }, [setRecentIncidents]);

  // Auto-select the newest running incident when the list updates
  useEffect(() => {
    if (!recentIncidents.length) return;
    const running = recentIncidents.find((i) => i.status === "running");
    const candidate = running ?? recentIncidents[0];
    if (candidate && candidate.id !== activeId) {
      setActiveId(candidate.id);
      getIncident(candidate.id).then(setIncident);
    }
    // activeId intentionally omitted — we only want to react to list changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recentIncidents, setIncident]);

  // When the user clicks a sidebar incident, switch to it
  useEffect(() => {
    if (!activeIncidentId || activeIncidentId === activeId) return;
    setActiveId(activeIncidentId);
    getIncident(activeIncidentId).then(setIncident);
  }, [activeIncidentId, activeId, setIncident]);

  // Subscribe to SSE stream for the active incident
  useIncidentStream(activeId);

  // Fire confetti when the incident completes
  useEffect(() => {
    if (agentStatus !== "complete") return;
    const duration = 5 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };
    const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;
    const interval = window.setInterval(() => {
      const timeLeft = animationEnd - Date.now();
      if (timeLeft <= 0) return clearInterval(interval);
      const particleCount = 50 * (timeLeft / duration);
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
      confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
    }, 250);
    return () => clearInterval(interval);
  }, [agentStatus]);

  function handleIncidentStarted(id: string) {
    setActiveId(id);
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
          <IncidentCompleteOverlay
            show={agentStatus === "complete"}
            toolCalls={incident?.tool_calls ?? []}
          />
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

      {!incident && (
        <div className="flex-1 flex items-center justify-center text-zinc-400">
          <div className="text-center">
            <p className="text-4xl mb-3">📬</p>
            <p className="text-base font-medium text-zinc-600">Waiting for an incident</p>
            <p className="text-sm text-zinc-400">
              The poller checks your inbox every 60 seconds. Incidents will appear here automatically.
            </p>
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

  const final =
    status === "complete" || status === "failed"
      ? Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)
      : elapsed;

  return <span>{final}s elapsed</span>;
}
