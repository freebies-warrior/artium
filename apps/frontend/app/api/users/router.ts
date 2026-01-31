import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);

  const limit = searchParams.get("limit") ?? "9";
  const cursor = searchParams.get("cursor");
  const q = searchParams.get("q");

  const backend = process.env.NEXT_PUBLIC_BACKEND_URL; // e.g. http://localhost:8080
  if (!backend) {
    return NextResponse.json({ message: "Missing NEXT_PUBLIC_BACKEND_URL" }, { status: 500 });
  }

  const qs = new URLSearchParams();
  qs.set("limit", limit);
  if (cursor) qs.set("cursor", cursor);
  if (q) qs.set("q", q);

  const r = await fetch(`${backend}/users?${qs.toString()}`, {
    method: "GET",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
  });

  const text = await r.text();
  try {
    const data = text ? JSON.parse(text) : {};
    return NextResponse.json(data, { status: r.status });
  } catch {
    return NextResponse.json({ message: text || "Bad response" }, { status: r.status });
  }
}
