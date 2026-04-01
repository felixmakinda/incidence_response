import clsx from "clsx";
import type { ToolStatus } from "@/types";

const CONFIG: Record<ToolStatus | "info", string> = {
  pending: "bg-zinc-400",
  running: "bg-blue-500 animate-pulse",
  success: "bg-green-500",
  failed: "bg-red-500",
  info: "bg-zinc-400",
};

export function StatusDot({ status }: { status: ToolStatus | "info" }) {
  return (
    <span className={clsx("inline-block w-2.5 h-2.5 rounded-full shrink-0", CONFIG[status])} />
  );
}
