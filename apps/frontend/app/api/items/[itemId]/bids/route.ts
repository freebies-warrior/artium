import { NextResponse } from "next/server";
import { cookies } from "next/headers";

export async function POST(
  req: Request,
  ctx: { params: Promise<{ itemId: string }> } // ✅ params is a Promise in your Next version
) {
  const backend = process.env.BACKEND_URL;
  if (!backend) throw new Error("BACKEND_URL is not defined");

  const { itemId } = await ctx.params; // ✅ unwrap params
  const token = (await cookies()).get("token")?.value;

  if (!token) {
    return NextResponse.json({ message: "UNAUTHORIZED" }, { status: 401 });
  }

  const body = await req.json();

  const backendRes = await fetch(`${backend}/items/${itemId}/bids`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`, // ✅ server-side Bearer
    },
    body: JSON.stringify(body),
  });

  const text = await backendRes.text();
  const data = text ? JSON.parse(text) : {};

  return NextResponse.json(data, { status: backendRes.status });
}
