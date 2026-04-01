"use client";

import clsx from "clsx";
import { SEVERITY_COLORS } from "@/lib/constants";
import { useIncidentStore } from "@/store/incidentStore";
import { IntegrationStatus } from "./IntegrationStatus";
import type { Incident } from "@/types";

function IncidentRow({ incident, isActive, onClick }: { incident: Incident; isActive: boolean; onClick: () => void }) {
  const timeStr = incident.started_at
    ? new Date(incident.started_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "—";

  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-full text-left px-3 py-2.5 rounded-lg transition-colors border",
        isActive
          ? "bg-blue-50 border-blue-200 text-blue-800"
          : "bg-transparent border-transparent hover:bg-zinc-100 text-zinc-700"
      )}
    >
      <div className="flex items-center justify-between mb-0.5">
        <span className={clsx("text-[10px] font-bold px-1.5 py-0.5 rounded", SEVERITY_COLORS[incident.severity])}>
          {incident.severity}
        </span>
        <span className="text-[10px] text-zinc-400">{timeStr}</span>
      </div>
      <p className="text-xs font-medium truncate">{incident.email.from_company}</p>
      <p className="text-[10px] text-zinc-500 truncate">{incident.email.subject}</p>
    </button>
  );
}

export function Sidebar() {
  const { recentIncidents, activeIncidentId, setActiveIncident } = useIncidentStore();

  return (
    <aside className="w-64 shrink-0 bg-white border-r border-zinc-200 flex flex-col">
      <div className="px-4 py-4 border-b border-zinc-100">
        <div className="flex items-center gap-2">
          <span className="text-lg">🚨</span>
          <div>
            <p className="text-sm font-bold text-zinc-900">Incident Response</p>
            <p className="text-[10px] text-zinc-400">Meridian SaaS Agent</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3">
        <p className="text-[10px] uppercase tracking-widest text-zinc-400 font-semibold mb-2 px-1">
          Recent Incidents
        </p>
        {recentIncidents.length === 0 && (
          <p className="text-xs text-zinc-400 italic px-1">No incidents yet</p>
        )}
        <div className="space-y-1">
          {recentIncidents.map((inc) => (
            <IncidentRow
              key={inc.id}
              incident={inc}
              isActive={inc.id === activeIncidentId}
              onClick={() => setActiveIncident(inc.id)}
            />
          ))}
        </div>
      </div>
      <IntegrationStatus />
    </aside>
  );
}
