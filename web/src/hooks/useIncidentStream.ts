"use client";

import { useEffect, useRef } from "react";
import { API_BASE } from "@/lib/constants";
import { useIncidentStore } from "@/store/incidentStore";
import type { StreamEvent } from "@/types";

export function useIncidentStream(incidentId: string | null) {
  const applyStreamEvent = useIncidentStore((s) => s.applyStreamEvent);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!incidentId) return;

    // Close any existing connection
    if (esRef.current) {
      esRef.current.close();
    }

    const es = new EventSource(`${API_BASE}/api/incidents/${incidentId}/stream`);
    esRef.current = es;

    es.onmessage = (e: MessageEvent) => {
      try {
        const event: StreamEvent = JSON.parse(e.data);
        if ((event as { event: string }).event === "heartbeat") return;
        applyStreamEvent(event);
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      // EventSource will auto-reconnect; event_bus replays history on reconnect
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [incidentId, applyStreamEvent]);
}
