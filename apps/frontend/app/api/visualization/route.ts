import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8080";

function getTokenFromCookie(req: Request) {
  const cookie = req.headers.get("cookie") ?? "";
  const token = cookie
    .split("; ")
    .find((c) => c.startsWith("token="))
    ?.split("=")[1];

  return token ?? null;
}

/**
 * POST /api/visualization
 * Proxies to: POST {BACKEND_URL}/visualizations
 */
export async function POST(req: Request) {
  const token = getTokenFromCookie(req);
  if (!token) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Not authenticated" } },
      { status: 401 }
    );
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { error: { code: "VALIDATION_ERROR", message: "Invalid JSON body" } },
      { status: 400 }
    );
  }

  try {
    const res = await fetch(`${BACKEND_URL}/visualizations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const text = await res.text();
    // Backend should return JSON, but handle non-JSON safely:
    const data = text ? safeJsonParse(text) : null;

    return NextResponse.json(data ?? {}, { status: res.status });
  } catch {
    return NextResponse.json(
      { error: { code: "INTERNAL_ERROR", message: "Failed to reach backend" } },
      { status: 500 }
    );
  }
}

/**
 * GET /api/visualization?job_id=...
 * Proxies to: GET {BACKEND_URL}/visualizations/{job_id}
 */
export async function GET(req: Request) {
  const token = getTokenFromCookie(req);
  if (!token) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Not authenticated" } },
      { status: 401 }
    );
  }

  const { searchParams } = new URL(req.url);
  const jobId = searchParams.get("job_id");

  if (!jobId) {
    return NextResponse.json(
      {
        error: {
          code: "VALIDATION_ERROR",
          message: "Missing required query param: job_id",
        },
      },
      { status: 400 }
    );
  }

  try {
    const res = await fetch(`${BACKEND_URL}/visualizations/${jobId}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    const text = await res.text();
    const data = text ? safeJsonParse(text) : null;

    return NextResponse.json(data ?? {}, { status: res.status });
  } catch {
    return NextResponse.json(
      { error: { code: "INTERNAL_ERROR", message: "Failed to reach backend" } },
      { status: 500 }
    );
  }
}

function safeJsonParse(text: string) {
  try {
    return JSON.parse(text);
  } catch {
    // Return raw text if backend didn't return JSON
    return { raw: text };
  }
}
