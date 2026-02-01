'use client'

import { useEffect, useState } from 'react'
import { extractUserId, type MeResponse } from '@/lib/auth'
import AddItemButton from './AddItemButton'

type UserHeaderProps = {
  userId: string
}

export default function UserHeader({ userId }: UserHeaderProps) {
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  /* ───────────── Get current user ───────────── */
  useEffect(() => {
    let cancelled = false

    async function run() {
      try {
        const res = await fetch('/api/auth/me', {
          credentials: 'include',
          cache: 'no-store',
        })

        if (!res.ok) {
          if (!cancelled) setCurrentUserId(null)
          return
        }

        const data = (await res.json().catch(() => null)) as MeResponse
        const uid = extractUserId(data)

        if (!cancelled) setCurrentUserId(uid)
      } catch {
        if (!cancelled) setCurrentUserId(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [])

  const isOwner = !loading && currentUserId === userId

  return (
    <div className="flex items-center gap-6 mb-8">
      <div className="h-24 w-24 rounded-full bg-neutral-700" />

      <div className="flex-1">
        <h1 className="text-2xl font-bold">Your Profile</h1>
        <p className="text-neutral-400">Manage your listings</p>
      </div>

      {/* ✅ Only show if owner */}
      {isOwner && <AddItemButton />}
    </div>
  )
}
