import { Suspense } from 'react'
import UserClient from './UserClient'

export default function UserPage() {
  return (
    <Suspense fallback={<div className="pt-20 text-center">Loading…</div>}>
      <UserClient />
    </Suspense>
  )
}
