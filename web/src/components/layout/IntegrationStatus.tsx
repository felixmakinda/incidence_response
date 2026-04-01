"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { API_BASE } from "@/lib/constants";

interface AuthStatus {
  google: { configured: boolean; authenticated: boolean };
  slack: { configured: boolean };
  jira: { configured: boolean };
}

function Pill({ label, active, href }: { label: string; active: boolean; href?: string }) {
  const base = clsx(
    "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border transition-colors",
    active
      ? "bg-green-50 text-green-700 border-green-200"
      : "bg-zinc-50 text-zinc-400 border-zinc-200"
  );

  if (!active && href) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={clsx(base, "hover:border-blue-300 hover:text-blue-600 cursor-pointer")}>
        <span className={clsx("w-1.5 h-1.5 rounded-full", active ? "bg-green-500" : "bg-zinc-300")} />
        {label}
        <span className="text-[9px] opacity-60">connect</span>
      </a>
    );
  }

  return (
    <span className={base}>
      <span className={clsx("w-1.5 h-1.5 rounded-full", active ? "bg-green-500" : "bg-zinc-300")} />
      {label}
    </span>
  );
}

export function IntegrationStatus() {
  const [status, setStatus] = useState<AuthStatus | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/auth/status`)
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => {});

    const id = setInterval(() => {
      fetch(`${API_BASE}/api/auth/status`)
        .then((r) => r.json())
        .then(setStatus)
        .catch(() => {});
    }, 10000);
    return () => clearInterval(id);
  }, []);

  if (!status) return null;

  const googleOk = status.google.authenticated;
  const slackOk = status.slack.configured;
  const jiraOk = status.jira.configured;

  return (
    <div className="px-3 py-2 border-t border-zinc-100">
      <p className="text-[9px] uppercase tracking-widest text-zinc-400 font-semibold mb-1.5">Integrations</p>
      <div className="flex flex-wrap gap-1">
        <Pill
          label="Google"
          active={googleOk}
          href={googleOk ? undefined : `${API_BASE}/api/auth/google`}
        />
        <Pill label="Slack" active={slackOk} />
        <Pill label="Jira" active={jiraOk} />
      </div>
      {!googleOk && status.google.configured && (
        <a
          href={`${API_BASE}/api/auth/google`}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 block text-center text-[10px] bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-1.5 font-medium transition-colors"
        >
          Connect Google Account
        </a>
      )}
      {!status.google.configured && (
        <p className="mt-1 text-[9px] text-zinc-400 leading-tight">
          Set <code className="bg-zinc-100 px-0.5 rounded">GOOGLE_CLIENT_ID</code> in api/.env to enable real Gmail
        </p>
      )}
    </div>
  );
}
