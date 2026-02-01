import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ userId: string }> }
) {
  const backend = process.env.BACKEND_URL
  if (!backend) throw new Error('BACKEND_URL is not defined')

  const { userId } = await ctx.params

  // Attach Bearer if token exists (same pattern as your items route)
  const token = (await cookies()).get('token')?.value

  const backendRes = await fetch(`${backend}/users/${userId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: 'no-store',
  })

  const text = await backendRes.text()

  // Safe JSON parse (backend might return empty/non-JSON on errors)
  let data: any = {}
  try {
    data = text ? JSON.parse(text) : {}
  } catch {
    data = { raw: text }
  }

  return NextResponse.json(data, { status: backendRes.status })
}
