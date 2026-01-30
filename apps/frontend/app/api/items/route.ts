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

export async function POST(req: Request) {
  const backend = process.env.BACKEND_URL
  if (!backend) {
    return NextResponse.json(
      { message: 'BACKEND_URL not set' },
      { status: 500 }
    )
  }

  const token = (await cookies()).get('token')?.value
  if (!token) {
    return NextResponse.json({ message: 'UNAUTHORIZED' }, { status: 401 })
  }

  const body = await req.json()

  const backendRes = await fetch(`${backend}/items`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })

  const text = await backendRes.text()
  const data = text ? JSON.parse(text) : {}

  return NextResponse.json(data, { status: backendRes.status })
}