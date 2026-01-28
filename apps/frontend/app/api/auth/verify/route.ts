import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  if (!process.env.BACKEND_URL) {
    throw new Error('BACKEND_URL is not defined')
  }

  const body = await req.json()

  const backendRes = await fetch(`${process.env.BACKEND_URL}/auth/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  const data = await backendRes.json()

  return NextResponse.json(data, { status: backendRes.status })
}
