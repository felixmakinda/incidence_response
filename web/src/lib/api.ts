import { API_BASE } from "./constants";
import type { Incident, MockEmail } from "@/types";

export async function triggerIncident(email?: MockEmail, severity = "P0"): Promise<{ incident_id: string }> {
  const res = await fetch(`${API_BASE}/api/incidents/trigger`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email_id: email?.id ?? null,
      severity,
      from_address: email?.from_address,
      from_company: email?.from_company,
      subject: email?.subject,
      body: email?.body,
    }),
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
