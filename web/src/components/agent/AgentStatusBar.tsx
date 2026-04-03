import clsx from "clsx";
import { Spinner } from "@/components/ui/Spinner";

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: React.ReactNode }> = {
  idle: { label: "Idle — waiting for incident", color: "text-zinc-500", bg: "bg-zinc-50 border-zinc-200", icon: <span className="text-lg">🤖</span> },
  thinking: { label: "Agent is reasoning...", color: "text-purple-700", bg: "bg-purple-50 border-purple-200", icon: <span className="text-lg">🧠</span> },
  calling_tool: { label: "Executing tool call...", color: "text-blue-700", bg: "bg-blue-50 border-blue-200", icon: <span className="text-lg">⚡</span> },
  complete: { label: "Incident response complete", color: "text-green-700", bg: "bg-green-50 border-green-200", icon: <img src="/svgs/accept-check.svg" className="w-5 h-5" alt="complete" /> },
  failed: { label: "Agent encountered an error", color: "text-red-700", bg: "bg-red-50 border-red-200", icon: <span className="text-lg">❌</span> },
};

export function AgentStatusBar({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.idle;
  const isActive = status === "thinking" || status === "calling_tool";

  return (
    <div className={clsx("flex items-center gap-3 px-4 py-2.5 rounded-xl border transition-all", cfg.bg)}>
      <span className="text-lg">{cfg.icon}</span>
      <div className="flex-1">
        <p className={clsx("text-sm font-medium", cfg.color)}>{cfg.label}</p>
      </div>
      {isActive && <Spinner size="sm" className={cfg.color} />}
    </div>
  );
}
