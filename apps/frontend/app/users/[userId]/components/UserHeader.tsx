'use client'

import { useEffect, useState } from 'react'
import { extractUserId, type MeResponse } from '@/lib/auth'
import AddItemButton from './AddItemButton'

type UserHeaderProps = {
  userId: string
}

// Adjust this to match your backend response shape
type UserDetailsResponse =
  | { id: string; username: string | null }

function extractUsername(payload: UserDetailsResponse | null): string | null {
  if (!payload) return null
  const c = (payload as any)?.username
  if (typeof c === 'string') return c

  return null
}

export default function UserHeader({ userId }: UserHeaderProps) {
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const [loadingMe, setLoadingMe] = useState(true)

  const [username, setUsername] = useState<string | null>(null)
  const [loadingUser, setLoadingUser] = useState(true)

  /* ───────────── Get current user (me) ───────────── */
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
        if (!cancelled) setLoadingMe(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [])

  /* ───────────── Get profile user's username ───────────── */
  useEffect(() => {
    let cancelled = false

    async function run() {
      try {
        setLoadingUser(true)
        setUsername(null)

        if (!userId) return

        // Change the route to match your backend:
        // e.g. /api/users/:userId, /api/user/:userId, etc.
        const res = await fetch(`/api/users/${userId}`, {
          cache: 'no-store',
        })

        if (!res.ok) return

        const data = (await res.json().catch(() => null)) as UserDetailsResponse
        console.log(data);
        const name = extractUsername(data)
        if (!cancelled) setUsername(name)
      } catch {
        if (!cancelled) setUsername(null)
      } finally {
        if (!cancelled) setLoadingUser(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [userId])

  const isOwner = !loadingMe && currentUserId === userId

  const title = loadingUser ? 'Loading User…' : username?.trim() || 'User Profile'

  return (
    <div className="flex items-center gap-6 mb-8">
      <div className="h-24 w-24 rounded-full bg-neutral-700" />

      <div className="flex-1">
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-neutral-400">
          {isOwner ? 'Manage your listings' : 'View listings'}
        </p>
      </div>

      {/* ✅ Only show if owner */}
      {isOwner && <AddItemButton />}
    </div>
  )
}
