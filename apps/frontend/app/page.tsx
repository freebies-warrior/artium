'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useState } from 'react'

export default function Home() {
  const params = useSearchParams()
  const router = useRouter()
  const verifyStatus = params.get('verify')

  // local UI-only state: whether banner is dismissed
  const [dismissed, setDismissed] = useState(false)

  let banner: string | null = null

  if (!dismissed) {
    if (verifyStatus === 'failed') {
      banner = 'This verification link is invalid or has expired.'
    } else if (verifyStatus === 'invalid') {
      banner = 'Invalid verification link.'
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6">
      {banner && (
        <div className="fixed top-20 left-0 right-0 z-40 flex justify-center px-4">
          <div className="relative w-full max-w-4xl bg-red-100 border border-red-300 rounded-lg px-4 py-3 text-red-700 text-center shadow">
            <span>{banner}</span>

            <button
              onClick={() => {
                setDismissed(true)
                router.replace('/', { scroll: false })
              }}
              className="absolute right-4 top-1/2 -translate-y-1/2 font-bold"
              aria-label="Close banner"
            >
              ×
            </button>
          </div>
        </div>
      )}

      <h1 className="text-5xl font-bold tracking-tight">Artium</h1>
      <p className="text-neutral-400">AI-powered art auction & evaluation</p>
    </main>
  )
}
