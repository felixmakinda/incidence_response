import { API_BASE } from "./constants";
import type { Incident, MockEmail } from "@/types";

export async function triggerIncident(emailId?: string, severity = "P0"): Promise<{ incident_id: string }> {
  const res = await fetch(`${API_BASE}/api/incidents/trigger`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email_id: emailId ?? null, severity }),
  });
  if (!res.ok) throw new Error(`Failed to trigger incident: ${res.statusText}`);
  return res.json();
}

export async function getIncident(incidentId: string): Promise<Incident> {
  const res = await fetch(`${API_BASE}/api/incidents/${incidentId}`);
  if (!res.ok) throw new Error(`Failed to fetch incident: ${res.statusText}`);
  return res.json();
}

export async function listIncidents(): Promise<Incident[]> {
  const res = await fetch(`${API_BASE}/api/incidents/`);
  if (!res.ok) return [];
  return res.json();
}

export async function listEmails(): Promise<MockEmail[]> {
  const res = await fetch(`${API_BASE}/api/emails/`);
  if (!res.ok) return [];
  return res.json();
}
