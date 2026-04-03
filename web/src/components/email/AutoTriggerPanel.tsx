"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { API_BASE } from "@/lib/constants";

interface PollerStatus {
  running: boolean;
  last_checked_at: string | null;
  last_triggered_at: string | null;
  last_error: string | null;
  emails_scanned: number;
  incidents_triggered: number;
}

interface ImapStatus {
  imap_configured: boolean;
  smtp_configured: boolean;
  imap_host: string;
  screening_threshold: number;
  processed_message_count: number;
  poller: PollerStatus | null;
}

function secondsAgo(iso: string | null): string {
  if (!iso) return "never";
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 5) return "just now";
  if (secs < 60) return `${secs}s ago`;
  return `${Math.floor(secs / 60)}m ago`;
}

export function AutoTriggerPanel() {
  const [status, setStatus] = useState<ImapStatus | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const res = await fetch("/api/gmail/watch");
        if (res.ok) {
          const data = await res.json();
          setStatus(data);
        }
      } catch {}
    }

    fetchStatus();
    const pollId = setInterval(fetchStatus, 15000);
    // Re-render every 5s so relative timestamps stay fresh
    const tickId = setInterval(() => setTick((t) => t + 1), 5000);
    return () => {
      clearInterval(pollId);
      clearInterval(tickId);
    };
  }, []);

  const poller = status?.poller ?? null;

  return (
    <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-100">
        <span className="text-lg">📬</span>
        <span className="text-sm font-semibold text-zinc-800">Auto-Trigger</span>
        <span className="text-xs text-zinc-400">IMAP polling + LLM screening</span>
      </div>

      <div className="px-4 py-3 space-y-2">
        {/* Config + poller status chips */}
        <div className="flex flex-wrap gap-2">
          <StatusChip
            label="IMAP"
            ok={status?.imap_configured ?? false}
            hint="Set IMAP_EMAIL_HOST, FROM_EMAIL, GOOGLE_APP_PASSWORD in api/.env"
          />
          <StatusChip
            label="SMTP"
            ok={status?.smtp_configured ?? false}
            hint="Set SMTP_EMAIL_HOST, FROM_EMAIL, GOOGLE_APP_PASSWORD in api/.env"
          />
          <StatusChip
            label="Poller"
            ok={poller?.running ?? false}
            hint="Starts automatically when IMAP is configured"
          />
        </div>

        {/* Poller activity */}
        {poller?.running && (
          <div className="text-xs text-zinc-500 space-y-0.5">
            <p>
              Last checked:{" "}
              <span className="font-medium text-zinc-700">
                {secondsAgo(poller.last_checked_at)}
              </span>
              {poller.last_triggered_at && (
                <>
                  {" · "}Last triggered:{" "}
                  <span className="font-medium text-zinc-700">
                    {secondsAgo(poller.last_triggered_at)}
                  </span>
                </>
              )}
            </p>
            <p>
              Scanned:{" "}
              <span className="font-medium text-zinc-700">{poller.emails_scanned}</span>
              {" emails · Incidents triggered: "}
              <span className="font-medium text-zinc-700">{poller.incidents_triggered}</span>
            </p>
          </div>
        )}

        {/* Screening threshold */}
        {status && (
          <p className="text-xs text-zinc-500">
            LLM screening threshold:{" "}
            <span className="font-semibold text-zinc-700">
              {Math.round(status.screening_threshold * 100)}% confidence
            </span>
            {status.imap_host && (
              <>
                {" · "}
                <span className="text-zinc-400">{status.imap_host}</span>
              </>
            )}
          </p>
        )}

        {/* Poller error */}
        {poller?.last_error && (
          <div className="text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2 border border-amber-200">
            <span className="font-medium">Poller error: </span>
            {poller.last_error}
          </div>
        )}

        {/* Config missing warning */}
        {status && !status.imap_configured && (
          <div className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2 border border-amber-200">
            <p>
              Set{" "}
              <code className="bg-amber-100 px-0.5 rounded">IMAP_EMAIL_HOST</code>,{" "}
              <code className="bg-amber-100 px-0.5 rounded">FROM_EMAIL</code>, and{" "}
              <code className="bg-amber-100 px-0.5 rounded">GOOGLE_APP_PASSWORD</code>{" "}
              in <code className="bg-amber-100 px-0.5 rounded">api/.env</code> to enable
              automatic inbox polling.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusChip({ label, ok, hint }: { label: string; ok: boolean; hint: string }) {
  return (
    <span
      title={ok ? undefined : hint}
      className={clsx(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border",
        ok
          ? "bg-green-50 text-green-700 border-green-200"
          : "bg-zinc-50 text-zinc-400 border-zinc-200 cursor-help"
      )}
    >
      <span className={clsx("w-1.5 h-1.5 rounded-full", ok ? "bg-green-500" : "bg-zinc-300")} />
      {label}
    </span>
  );
}
