'use client'

import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

export default function VerifyPage() {
  const router = useRouter()
  const params = useSearchParams()
  const token = params.get('token')

  useEffect(() => {
    if (!token) {
      router.replace('/?verify=invalid')
      return
    }

    const verify = async () => {
      const res = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      })

      if (!res.ok) {
        router.replace('/?verify=failed')
        return
      }

      router.replace('/?verify=success')
    }

    verify()
  }, [token, router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-neutral-500">Verifying your email…</p>
    </div>
  )
}
