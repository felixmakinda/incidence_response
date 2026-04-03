"use client";

import { useState } from "react";
import clsx from "clsx";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { SEVERITY_COLORS } from "@/lib/constants";
import { triggerIncident } from "@/lib/api";
import { useIncidentStore } from "@/store/incidentStore";
import type { MockEmail, Incident } from "@/types";
import { getIncident } from "@/lib/api";

interface EmailTriggerCardProps {
  emails: MockEmail[];
  onIncidentStarted: (incidentId: string) => void;
}

export function EmailTriggerCard({ emails, onIncidentStarted }: EmailTriggerCardProps) {
  const [selectedEmailId, setSelectedEmailId] = useState(emails[0]?.id || "");
  const [expanded, setExpanded] = useState(true);
  const [loading, setLoading] = useState(false);
  const setIncident = useIncidentStore((s) => s.setIncident);

  const selectedEmail = emails.find((e) => e.id === selectedEmailId) || emails[0];

  async function handleTrigger() {
    if (!selectedEmail) return;
    setLoading(true);
    try {
      const { incident_id } = await triggerIncident(selectedEmail, "P0");
      // Fetch initial incident snapshot and store it
      const incident: Incident = await getIncident(incident_id);
      setIncident(incident);
      onIncidentStarted(incident_id);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-100">
        <div className="flex items-center gap-2">
          <img src="/svgs/mailbox.svg" className="w-5 h-5" alt="" />
          <span className="text-sm font-semibold text-zinc-800">Incoming Customer Email</span>
          <Badge variant="danger">P0 Trigger</Badge>
        </div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-zinc-400 hover:text-zinc-600 transition-colors text-sm"
        >
          {expanded ? "▲" : "▼"}
        </button>
      </div>

      {expanded && selectedEmail && (
        <div className="p-4 space-y-3">
          {/* Email selector */}
          {emails.length > 1 && (
            <div>
              <label className="text-xs text-zinc-500 font-medium block mb-1">Select scenario:</label>
              <select
                value={selectedEmailId}
                onChange={(e) => setSelectedEmailId(e.target.value)}
                className="text-sm text-zinc-800 border border-zinc-200 rounded-lg px-3 py-1.5 w-full bg-zinc-50 focus:outline-none focus:ring-2 focus:ring-blue-200"
              >
                {emails.map((e) => (
                  <option key={e.id} value={e.id} className="bg-white text-zinc-800">
                    {e.from_company} — {e.subject.slice(0, 50)}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Email preview */}
          <div className="bg-zinc-50 rounded-lg p-3 border border-zinc-200 space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-xs text-zinc-500 font-medium w-12">From:</span>
              <span className="text-xs text-zinc-800">{selectedEmail.from_address}</span>
              <Badge variant="warning">{selectedEmail.from_company}</Badge>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-xs text-zinc-500 font-medium w-12 shrink-0">Subject:</span>
              <span className="text-xs text-zinc-800 font-medium">{selectedEmail.subject}</span>
            </div>
            <div className="mt-2 pt-2 border-t border-zinc-200">
              <pre className="text-xs text-zinc-600 whitespace-pre-wrap font-sans leading-relaxed max-h-36 overflow-y-auto">
                {selectedEmail.body}
              </pre>
            </div>
          </div>

          {/* Trigger button */}
          <button
            onClick={handleTrigger}
            disabled={loading}
            className={clsx(
              "w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all",
              loading
                ? "bg-zinc-200 text-zinc-500 cursor-not-allowed"
                : "bg-red-600 hover:bg-red-700 text-white shadow-sm hover:shadow-md"
            )}
          >
            {loading ? (
              <>
                <Spinner size="sm" className="text-zinc-500" />
                Starting agent...
              </>
            ) : (
              <>
                <span>🚨</span>
                Trigger Incident Response
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
