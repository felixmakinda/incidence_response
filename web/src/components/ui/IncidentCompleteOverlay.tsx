"use client";

import { useEffect, useState } from "react";
import type { ToolCallRecord } from "@/types";

const TOOL_META: Record<string, { icon: string; label: string }> = {
  gmail_reply: { icon: "/svgs/gmail.svg", label: "Customer Notified" },
  create_meet_link: {
    icon: "/svgs/google-meet.svg",
    label: "War Room Created",
  },
  create_calendar_event: {
    icon: "/svgs/google-calendar.svg",
    label: "Meeting Scheduled",
  },
  create_jira_ticket: { icon: "/svgs/jira.svg", label: "Ticket Filed" },
  post_slack_message: { icon: "/svgs/slack.svg", label: "Team Alerted" },
  create_google_doc: {
    icon: "/svgs/google-docs.svg",
    label: "Runbook Created",
  },
};

interface Props {
  show: boolean;
  toolCalls: ToolCallRecord[];
}

export function IncidentCompleteOverlay({ show, toolCalls }: Props) {
  const [timedOut, setTimedOut] = useState(false);
  const [prevShow, setPrevShow] = useState(show);

  // Adjust state during render (React-recommended pattern) instead of in an effect
  if (prevShow !== show) {
    setPrevShow(show);
    if (show) setTimedOut(false); // reset timer when show transitions to true
  }

  // Only call setState in a callback (setTimeout), never synchronously in the effect body
  useEffect(() => {
    if (!show) return;
    const t = setTimeout(() => setTimedOut(true), 6200);
    return () => clearTimeout(t);
  }, [show]);

  const visible = show && !timedOut;
  if (!visible) return null;

  const succeeded = toolCalls.filter((tc) => tc.status === "success");

  return (
    <>
      <style>{`
        @keyframes incidentZoomFloat {
          0%   { opacity: 0; transform: translate(-50%, -50%) scale(0.25); }
          15%  { opacity: 1; transform: translate(-50%, -50%) scale(1.04); }
          25%  { transform: translate(-50%, -50%) scale(1); }
          70%  { opacity: 1; transform: translate(-50%, -56%) scale(1); }
          100% { opacity: 0; transform: translate(-50%, -72%) scale(0.97); }
        }
        .incident-complete-card {
          animation: incidentZoomFloat 6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
      `}</style>
      <div className="incident-complete-card fixed top-1/2 left-1/2 z-[10000] pointer-events-none text-center w-max max-w-sm">
        <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-green-200 px-7 py-5 space-y-3">
          {/* Headline */}
          <div className="flex items-center justify-center gap-2.5">
            <img src="/svgs/accept-check.svg" className="w-7 h-7" alt="" />
            <h2 className="text-xl font-bold text-green-700 tracking-tight">
              Incident Reported
            </h2>
          </div>

          <p className="text-xs text-zinc-400 font-medium uppercase tracking-widest">
            Full response executed automatically
          </p>

          {/* Completed actions */}
          {succeeded.length > 0 && (
            <div className="grid grid-cols-2 gap-1.5 pt-1">
              {succeeded.map((tc) => {
                const meta = TOOL_META[tc.tool_name];
                if (!meta) return null;
                return (
                  <div
                    key={tc.id}
                    className="flex items-center gap-1.5 text-xs text-zinc-700 bg-zinc-50 rounded-lg px-2.5 py-1.5 border border-zinc-100"
                  >
                    <img src={meta.icon} className="w-4 h-4 shrink-0" alt="" />
                    <span>{meta.label}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
