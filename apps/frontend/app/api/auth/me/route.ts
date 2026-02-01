import { NextResponse } from 'next/server'
import jwt from 'jsonwebtoken'

interface JwtPayload {
  user_id?: string
  id?: string
  sub?: string
}

export async function GET(req: Request) {
  const token = req.headers
    .get('cookie')
    ?.split('; ')
    .find((c) => c.startsWith('token='))
    ?.slice(6)

  if (!token || !process.env.JWT_SECRET) {
    return NextResponse.json({ authenticated: false })
  }

  const payload = jwt.verify(
    token,
    process.env.JWT_SECRET!
  ) as JwtPayload | null

  if (!payload) {
    return NextResponse.json({ authenticated: false })
  }

  const userId = payload.user_id ?? payload.id ?? payload.sub
  if (!userId) {
    return NextResponse.json({ authenticated: false })
  }

  return NextResponse.json({
    authenticated: true,
    user_id: userId,
  })
}
