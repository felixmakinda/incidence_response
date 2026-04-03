"use client";

import { useState } from "react";
import clsx from "clsx";
import { ToolStatusBadge } from "./ToolStatusBadge";
import { TOOL_DISPLAY } from "@/lib/constants";
import type { ToolCallRecord } from "@/types";

const TOOL_ICONS: Record<string, string> = {
  gmail: "/svgs/gmail.svg",
  meet: "/svgs/google-meet.svg",
  calendar: "/svgs/google-calendar.svg",
  jira: "/svgs/jira.svg",
  slack: "/svgs/slack.svg",
  docs: "/svgs/google-docs.svg",
};

interface ToolCardProps {
  toolCall: ToolCallRecord;
}

export function ToolCard({ toolCall }: ToolCardProps) {
  const [paramsOpen, setParamsOpen] = useState(false);
  const [resultOpen, setResultOpen] = useState(false);

  const display = TOOL_DISPLAY[toolCall.tool_name] || {
    label: toolCall.display_name,
    color: "text-zinc-600",
    bgColor: "bg-zinc-50",
    borderColor: "border-zinc-200",
  };
  const icon = TOOL_ICONS[toolCall.icon];
  const isActive = toolCall.status === "running" || toolCall.status === "success";

  return (
    <div
      className={clsx(
        "rounded-xl border transition-all duration-300",
        display.borderColor,
        toolCall.status === "running" && "shadow-md shadow-blue-100 ring-1 ring-blue-300",
        toolCall.status === "success" && "shadow-sm",
        toolCall.status === "failed" && "border-red-300 bg-red-50",
        toolCall.status !== "failed" && display.bgColor
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          {icon
            ? <img src={icon} className="w-8 h-8" alt="" />
            : <span className="text-xl">🔧</span>
          }
          <div>
            <p className={clsx("text-sm font-semibold", display.color)}>{toolCall.display_name}</p>
            {toolCall.depends_on.length > 0 && (
              <p className="text-xs text-zinc-400">Requires: {toolCall.depends_on.map((d) => TOOL_DISPLAY[d]?.label || d).join(", ")}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {toolCall.duration_ms && (
            <span className="text-xs text-zinc-400">{toolCall.duration_ms}ms</span>
          )}
          <ToolStatusBadge status={toolCall.status} />
        </div>
      </div>

      {/* Params */}
      {isActive && Object.keys(toolCall.params).length > 0 && (
        <div className="border-t border-current/10 px-4 py-2">
          <button
            onClick={() => setParamsOpen((v) => !v)}
            className="flex items-center gap-1 text-xs font-medium text-zinc-500 hover:text-zinc-700 transition-colors"
          >
            <span className={clsx("transition-transform", paramsOpen && "rotate-90")}>▶</span>
            Parameters sent
          </button>
          {paramsOpen && (
            <pre className="mt-2 text-xs bg-white/70 rounded p-2 overflow-x-auto text-zinc-700 border border-zinc-200 max-h-40">
              {JSON.stringify(toolCall.params, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Result */}
      {toolCall.status === "success" && toolCall.result && (
        <div className="border-t border-current/10 px-4 py-2">
          <button
            onClick={() => setResultOpen((v) => !v)}
            className="flex items-center gap-1 text-xs font-medium text-green-600 hover:text-green-800 transition-colors"
          >
            <span className={clsx("transition-transform", resultOpen && "rotate-90")}>▶</span>
            Result received
          </button>
          {resultOpen && (
            <pre className="mt-2 text-xs bg-white/70 rounded p-2 overflow-x-auto text-zinc-700 border border-green-200 max-h-40">
              {JSON.stringify(toolCall.result, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Error */}
      {toolCall.status === "failed" && toolCall.error && (
        <div className="border-t border-red-200 px-4 py-2">
          <p className="text-xs text-red-600 font-medium">Error: {toolCall.error}</p>
        </div>
      )}
    </div>
  );
}
