import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ itemId: string }> }
) {
  const backend = process.env.BACKEND_URL;
  if (!backend) throw new Error("BACKEND_URL is not defined");

  const { itemId } = await ctx.params;

  // If your backend allows public GET /items/:id, you can remove auth.
  // Keeping it consistent with bids: attach Bearer if token exists.
  const token = (await cookies()).get("token")?.value;

  const backendRes = await fetch(`${backend}/items/${itemId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: "no-store",
  });

  const text = await backendRes.text();
  const data = text ? JSON.parse(text) : {};

  return NextResponse.json(data, { status: backendRes.status });
}
