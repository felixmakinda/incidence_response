/**
 * Public webhook endpoint hosted on Vercel.
 * Google Cloud Pub/Sub pushes here when a new Gmail message arrives.
 *
 * Flow:
 *   Gmail → Pub/Sub push → POST /api/gmail/webhook (this route)
 *   → decode message → fetch email from Gmail API
 *   → forward to FastAPI for LLM screening + agent trigger
 */

import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL!;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || "";
const PUBSUB_TOKEN = process.env.GMAIL_PUBSUB_TOKEN || "";

export async function POST(request: NextRequest) {
  // Verify Pub/Sub token (set as a query param on the push subscription URL)
  const { searchParams } = new URL(request.url);
  if (PUBSUB_TOKEN && searchParams.get("token") !== PUBSUB_TOKEN) {
    return NextResponse.json({ error: "Invalid token" }, { status: 401 });
  }

  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  // Pub/Sub push message format
  const message = (body.message as Record<string, string>) || {};
  const dataB64 = message.data || "";

  if (!dataB64) {
    // Acknowledge empty messages to prevent redelivery
    return NextResponse.json({ status: "ack_empty" });
  }

  let gmailNotification: { emailAddress?: string; historyId?: number };
  try {
    const decoded = Buffer.from(dataB64, "base64").toString("utf-8");
    gmailNotification = JSON.parse(decoded);
  } catch {
    return NextResponse.json({ error: "Decode failed" }, { status: 400 });
  }

  const historyId = gmailNotification.historyId?.toString();
  if (!historyId) {
    return NextResponse.json({ status: "ack_no_history" });
  }

  // Forward the raw Pub/Sub notification to FastAPI.
  // FastAPI has the Google OAuth credentials to fetch the actual email,
  // run LLM screening, and trigger the agent.
  try {
    const apiResponse = await fetch(`${API_BASE}/api/webhook/gmail/pubsub`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(WEBHOOK_SECRET ? { "x-webhook-secret": WEBHOOK_SECRET } : {}),
      },
      body: JSON.stringify(body),
    });

    if (!apiResponse.ok) {
      const err = await apiResponse.text();
      console.error("[gmail/webhook] FastAPI error:", err);
      // Still return 200 to Pub/Sub to avoid infinite redelivery
    }
  } catch (err) {
    console.error("[gmail/webhook] Failed to reach FastAPI:", err);
    // Return 200 to acknowledge — FastAPI being down shouldn't cause Pub/Sub
    // to keep retrying at high frequency
  }

  // Always return 200/204 to acknowledge Pub/Sub delivery
  return NextResponse.json({ status: "ok" });
}
