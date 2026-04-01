import clsx from "clsx";
import { Spinner } from "@/components/ui/Spinner";
import type { ToolStatus } from "@/types";

const CONFIG: Record<ToolStatus, { label: string; className: string }> = {
  pending: { label: "Pending", className: "bg-zinc-100 text-zinc-500" },
  running: { label: "Running", className: "bg-blue-100 text-blue-700" },
  success: { label: "Done", className: "bg-green-100 text-green-700" },
  failed: { label: "Failed", className: "bg-red-100 text-red-700" },
};

export function ToolStatusBadge({ status }: { status: ToolStatus }) {
  const cfg = CONFIG[status];
  return (
    <span className={clsx("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium", cfg.className)}>
      {status === "running" && <Spinner size="sm" className="w-3 h-3" />}
      {cfg.label}
    </span>
  );
}
