import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'

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
