"use client";

import clsx from "clsx";
import { TOOL_ORDER, TOOL_DISPLAY } from "@/lib/constants";
import type { ToolCallRecord, ToolStatus } from "@/types";

const TOOL_ICONS: Record<string, string> = {
  gmail_reply: "📧",
  create_meet_link: "📹",
  create_calendar_event: "📅",
  create_jira_ticket: "🎯",
  post_slack_message: "💬",
  create_google_doc: "📄",
};

const STATUS_STYLES: Record<ToolStatus, string> = {
  pending: "border-zinc-300 bg-zinc-50 text-zinc-400",
  running: "border-blue-400 bg-blue-50 text-blue-600 ring-2 ring-blue-200 animate-pulse",
  success: "border-green-400 bg-green-50 text-green-700",
  failed: "border-red-400 bg-red-50 text-red-600",
};

interface PipelineViewProps {
  toolCalls: ToolCallRecord[];
}

export function PipelineView({ toolCalls }: PipelineViewProps) {
  const callsByName = Object.fromEntries(toolCalls.map((tc) => [tc.tool_name, tc]));

  return (
    <div className="flex items-center gap-0 overflow-x-auto py-2">
      {TOOL_ORDER.map((toolName, idx) => {
        const tc = callsByName[toolName];
        const status: ToolStatus = tc?.status || "pending";
        const display = TOOL_DISPLAY[toolName];
        return (
          <div key={toolName} className="flex items-center shrink-0">
            {/* Step node */}
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  "w-14 h-14 rounded-xl border-2 flex flex-col items-center justify-center transition-all duration-300",
                  STATUS_STYLES[status]
                )}
              >
                <span className="text-xl">{TOOL_ICONS[toolName]}</span>
              </div>
              <p className={clsx("text-xs mt-1.5 font-medium text-center w-16 leading-tight", display?.color || "text-zinc-500")}>
                {display?.label || toolName}
              </p>
              {status === "success" && tc?.duration_ms && (
                <span className="text-[10px] text-zinc-400">{tc.duration_ms}ms</span>
              )}
            </div>

            {/* Connector arrow */}
            {idx < TOOL_ORDER.length - 1 && (
              <div className="relative flex items-center mx-1">
                <div className="w-6 h-0.5 bg-zinc-300" />
                <svg className="w-3 h-3 text-zinc-400 -ml-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                  />
                </svg>
                {/* Dependency badge between Meet and Calendar */}
                {TOOL_ORDER[idx] === "create_meet_link" && (
                  <span className="absolute -top-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-[9px] bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded-full border border-orange-200 font-medium">
                    needs URL
                  </span>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
