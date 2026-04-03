"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { API_BASE } from "@/lib/constants";

interface ImapStatus {
  imap_configured: boolean;
  smtp_configured: boolean;
  imap_host: string;
  screening_threshold: number;
  processed_message_count: number;
}

export function AutoTriggerPanel() {
  const [status, setStatus] = useState<ImapStatus | null>(null);

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
    const id = setInterval(fetchStatus, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-100">
        <span className="text-lg">📬</span>
        <span className="text-sm font-semibold text-zinc-800">Email Config</span>
        <span className="text-xs text-zinc-400">IMAP inbox + LLM screening</span>
      </div>

      <div className="px-4 py-3 space-y-2">
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
        </div>

        {status && (
          <p className="text-xs text-zinc-500">
            LLM screening threshold:{" "}
            <span className="font-semibold text-zinc-700">
              {Math.round(status.screening_threshold * 100)}% confidence
            </span>
            {" · "}
            <span className="text-zinc-400">
              {status.processed_message_count} emails processed
            </span>
            {status.imap_host && (
              <>
                {" · "}
                <span className="text-zinc-400">{status.imap_host}</span>
              </>
            )}
          </p>
        )}

        {status && !status.imap_configured && (
          <div className="text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2 border border-amber-200">
            <p>
              Set{" "}
              <code className="bg-amber-100 px-0.5 rounded">IMAP_EMAIL_HOST</code>,{" "}
              <code className="bg-amber-100 px-0.5 rounded">FROM_EMAIL</code>, and{" "}
              <code className="bg-amber-100 px-0.5 rounded">GOOGLE_APP_PASSWORD</code>{" "}
              in <code className="bg-amber-100 px-0.5 rounded">api/.env</code> to enable
              real inbox reading.
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
