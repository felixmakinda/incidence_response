"use client";

import clsx from "clsx";
import { TOOL_ORDER, TOOL_DISPLAY } from "@/lib/constants";
import type { ToolCallRecord, ToolStatus } from "@/types";

const TOOL_ICONS: Record<string, string> = {
  gmail_reply: "/svgs/gmail.svg",
  create_meet_link: "/svgs/google-meet.svg",
  create_calendar_event: "/svgs/google-calendar.svg",
  create_jira_ticket: "/svgs/jira.svg",
  post_slack_message: "/svgs/slack.svg",
  create_google_doc: "/svgs/google-docs.svg",
};

const STATUS_STYLES: Record<ToolStatus, string> = {
  pending: "border-zinc-200 bg-zinc-50 text-zinc-400",
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
    <div className="overflow-x-auto py-3">
      <div className="flex items-start min-w-max">
        {TOOL_ORDER.map((toolName, idx) => {
          const tc = callsByName[toolName];
          const status: ToolStatus = tc?.status || "pending";
          const display = TOOL_DISPLAY[toolName];
          return (
            <div key={toolName} className="flex items-start">
              {/* Node */}
              <div className="flex flex-col items-center w-16">
                <div
                  className={clsx(
                    "w-12 h-12 rounded-xl border-2 flex items-center justify-center transition-all duration-300",
                    STATUS_STYLES[status]
                  )}
                >
                  <img src={TOOL_ICONS[toolName]} className="w-6 h-6" alt={toolName} />
                </div>
                <p className={clsx("text-[10px] mt-1.5 font-medium text-center leading-tight w-14", display?.color || "text-zinc-500")}>
                  {display?.label || toolName}
                </p>
                {status === "success" && tc?.duration_ms && (
                  <span className="text-[9px] text-zinc-400 mt-0.5">{tc.duration_ms}ms</span>
                )}
              </div>

              {/* Connector — mt-[18px] centres it on the 48px (h-12) box */}
              {idx < TOOL_ORDER.length - 1 && (
                <div className="relative flex flex-col items-center mt-[18px]">
                  {TOOL_ORDER[idx] === "create_meet_link" && (
                    <span className="absolute -top-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-[9px] bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded-full border border-orange-200 font-medium">
                      needs URL
                    </span>
                  )}
                  <div className="flex items-center">
                    <div className="w-8 h-px bg-zinc-300" />
                    <svg className="w-3 h-3 text-zinc-400 -ml-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                      />
                    </svg>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
