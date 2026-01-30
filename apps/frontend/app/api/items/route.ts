import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

export async function GET(req: Request) {
  const backend = process.env.BACKEND_URL
  if (!backend) throw new Error('BACKEND_URL is not defined')

  const token = (await cookies()).get('token')?.value

  // Forward all query params (q, next_cursor, limit, etc.)
  const url = new URL(req.url)
  const qs = url.searchParams.toString()
  const backendUrl = qs ? `${backend}/items?${qs}` : `${backend}/items`

  const backendRes = await fetch(backendUrl, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: 'no-store',
  })

  const text = await backendRes.text()
  const data = text ? JSON.parse(text) : {}

  return NextResponse.json(data, { status: backendRes.status })
}
