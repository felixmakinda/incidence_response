"use client";

import { useEffect, useRef } from "react";
import clsx from "clsx";
import type { AgentThought, ThoughtType } from "@/types";

const TYPE_STYLES: Record<ThoughtType, { border: string; label: string; labelColor: string }> = {
  reasoning: { border: "border-l-purple-400", label: "Reasoning", labelColor: "text-purple-500" },
  decision: { border: "border-l-blue-400", label: "Decision", labelColor: "text-blue-500" },
  observation: { border: "border-l-green-400", label: "Observation", labelColor: "text-green-500" },
};

function ThoughtBubble({ thought, index }: { thought: AgentThought; index: number }) {
  const cfg = TYPE_STYLES[thought.type];
  const time = new Date(thought.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  return (
    <div
      className={clsx(
        "border-l-2 pl-3 py-1 transition-all",
        cfg.border,
        "animate-fade-in"
      )}
      style={{ animationDelay: `${Math.min(index * 30, 200)}ms` }}
    >
      <div className="flex items-center gap-2 mb-0.5">
        <span className={clsx("text-[10px] font-semibold uppercase tracking-wide", cfg.labelColor)}>
          {cfg.label}
        </span>
        <span className="text-[10px] text-zinc-400">{time}</span>
      </div>
      <p className="text-xs text-zinc-600 leading-relaxed">{thought.content}</p>
    </div>
  );
}

interface AgentThoughtStreamProps {
  thoughts: AgentThought[];
  agentStatus: string;
}

export function AgentThoughtStream({ thoughts, agentStatus }: AgentThoughtStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const userScrolled = useRef(false);

  useEffect(() => {
    if (!userScrolled.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [thoughts.length]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-1 mb-2">
        <h3 className="text-sm font-semibold text-zinc-700">Agent Reasoning</h3>
        <div className="flex items-center gap-1.5">
          {agentStatus === "thinking" && (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: "300ms" }} />
            </>
          )}
          {agentStatus === "complete" && <span className="text-xs text-green-500 font-medium">Complete</span>}
        </div>
      </div>

      <div
        ref={containerRef}
        onScroll={() => {
          const el = containerRef.current;
          if (!el) return;
          userScrolled.current = el.scrollTop + el.clientHeight < el.scrollHeight - 50;
        }}
        className="flex-1 overflow-y-auto space-y-3 pr-1"
      >
        {thoughts.length === 0 && (
          <p className="text-xs text-zinc-400 italic">Waiting for agent to start thinking...</p>
        )}
        {thoughts.map((t, i) => (
          <ThoughtBubble key={t.id} thought={t} index={i} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
