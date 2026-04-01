/**
 * Proxy endpoints to start/stop Gmail watch() from the dashboard UI.
 * These call the FastAPI which holds the Google OAuth credentials.
 */

import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL!;

export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action") || "start";

  const endpoint = action === "stop" ? "/api/watch/stop" : "/api/watch/start";

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, { method: "POST" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.ok ? 200 : res.status });
  } catch (err) {
    return NextResponse.json({ error: "Failed to reach API" }, { status: 503 });
  }
}

export async function GET() {
  try {
    const res = await fetch(`${API_BASE}/api/watch/status`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to reach API" }, { status: 503 });
  }
}
