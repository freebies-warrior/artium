import { NextResponse } from 'next/server'

type LoginBackendResponse = {
  token: string
  user: {
    id: string
    email: string
    verified: boolean
  }
}

export async function POST(req: Request) {
  if (!process.env.BACKEND_URL) {
    throw new Error('BACKEND_URL is not defined')
  }

  const body = await req.json()

  const backendRes = await fetch(`${process.env.BACKEND_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  const text = await backendRes.text()
  const data = (text ? JSON.parse(text) : {}) as LoginBackendResponse

  if (!backendRes.ok) {
    return NextResponse.json(data, {
      status: backendRes.status,
    })
  }

  const response = NextResponse.json({ user: data.user })

  response.cookies.set('token', data.token, {
    httpOnly: true,
    path: '/',
    maxAge: 60 * 60 * 24,
  })

  return response
}
