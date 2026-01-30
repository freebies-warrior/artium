import { Suspense } from 'react'
import VerifyClient from './VerifyClient'

export default function VerifyPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <p className="text-neutral-500">Verifying your email…</p>
        </div>
      }
    >
      <VerifyClient />
    </Suspense>
  )
}
