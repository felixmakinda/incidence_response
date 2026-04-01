"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { Spinner } from "@/components/ui/Spinner";

interface WatchStatus {
  google_authenticated: boolean;
  pubsub_configured: boolean;
  pubsub_topic: string;
  screening_threshold: number;
  processed_message_count: number;
}

export function AutoTriggerPanel() {
  const [status, setStatus] = useState<WatchStatus | null>(null);
  const [watchActive, setWatchActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastAction, setLastAction] = useState<string | null>(null);

  async function fetchStatus() {
    try {
      const res = await fetch("/api/gmail/watch");
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch {}
  }

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, 15000);
    return () => clearInterval(id);
  }, []);

  async function toggleWatch() {
    if (!status?.google_authenticated || !status?.pubsub_configured) return;
    setLoading(true);
    const action = watchActive ? "stop" : "start";
    try {
      const res = await fetch(`/api/gmail/watch?action=${action}`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setWatchActive(!watchActive);
        setLastAction(
          action === "start"
            ? `Watching inbox. Expires: ${data.expiration ? new Date(data.expiration).toLocaleDateString() : "7 days"}`
            : "Watch stopped."
        );
      }
    } catch {}
    setLoading(false);
  }

  const canActivate = status?.google_authenticated && status?.pubsub_configured;

  return (
    <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-100">
        <div className="flex items-center gap-2">
          <span className="text-lg">⚡</span>
          <span className="text-sm font-semibold text-zinc-800">Auto-Trigger</span>
          <span className="text-xs text-zinc-400">Gmail watch + LLM screening</span>
        </div>

        {/* Toggle */}
        <button
          onClick={toggleWatch}
          disabled={!canActivate || loading}
          className={clsx(
            "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none",
            watchActive ? "bg-green-500" : "bg-zinc-300",
            (!canActivate || loading) && "opacity-50 cursor-not-allowed"
          )}
        >
          {loading && <Spinner size="sm" className="absolute inset-0 m-auto text-white w-3 h-3" />}
          <span
            className={clsx(
              "inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform",
              watchActive ? "translate-x-6" : "translate-x-1"
            )}
          />
        </button>
      </div>

      <div className="px-4 py-3 space-y-2">
        {/* Status indicators */}
        <div className="flex flex-wrap gap-2">
          <StatusChip
            label="Google Auth"
            ok={status?.google_authenticated ?? false}
            hint="Visit /api/auth/google"
          />
          <StatusChip
            label="Pub/Sub"
            ok={status?.pubsub_configured ?? false}
            hint="Set GMAIL_PUBSUB_TOPIC"
          />
          <StatusChip
            label="Watching"
            ok={watchActive}
            hint="Toggle to activate"
          />
        </div>

        {/* Screening threshold */}
        {status && (
          <p className="text-xs text-zinc-500">
            LLM screening threshold:{" "}
            <span className="font-semibold text-zinc-700">
              {Math.round(status.screening_threshold * 100)}% confidence
            </span>
            {" · "}
            <span className="text-zinc-400">{status.processed_message_count} emails processed</span>
          </p>
        )}

        {lastAction && (
          <p className="text-xs text-green-600 font-medium">{lastAction}</p>
        )}

        {!canActivate && status && (
          <div className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2 border border-amber-200">
            {!status.google_authenticated && (
              <p>Connect your Google account to enable auto-trigger.</p>
            )}
            {status.google_authenticated && !status.pubsub_configured && (
              <p>
                Set <code className="bg-amber-100 px-0.5 rounded">GMAIL_PUBSUB_TOPIC</code> in
                {" "}api/.env and configure a Pub/Sub push subscription pointing to{" "}
                <code className="bg-amber-100 px-0.5 rounded">YOUR_VERCEL_URL/api/gmail/webhook</code>.
              </p>
            )}
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
