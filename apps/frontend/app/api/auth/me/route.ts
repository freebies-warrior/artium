import { NextResponse } from 'next/server'
import jwt from 'jsonwebtoken'
export async function GET(req: Request) {
  const token = req.headers
    .get('cookie')
    ?.split('; ')
    .find((c) => c.startsWith('token='))
    ?.slice(6)

  if (!token) {
    return NextResponse.json({ error: 'Missing token' }, { status: 401 })
  }
  console.log(token)
  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as any

    const userId = payload.user_id ?? payload.id ?? payload.sub
    if (!userId) {
      return NextResponse.json(
        { error: 'Token missing user id' },
        { status: 401 }
      )
    }

    return NextResponse.json({
      authenticated: true,
      user_id: userId,
    })
  } catch (err) {
    return NextResponse.json({ error: 'Invalid token' }, { status: 401 })
  }
}
