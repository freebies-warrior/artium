'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { usePathname } from 'next/navigation'

interface AuthMeResponse {
  authenticated: boolean
  user_id?: string
}

export default function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [userId, setUserId] = useState<string | null>(null)
  const router = useRouter()
  const pathname = usePathname()

  // 🔍 Check login status
  useEffect(() => {
    const checkAuth = async () => {
      const res = await fetch('/api/auth/me', {
        credentials: 'include',
      })
      const data: AuthMeResponse = await res.json()
      console.log(data)
      if (data.authenticated && data.user_id) {
        setIsLoggedIn(true)
        setUserId(data.user_id)
      } else {
        setIsLoggedIn(false)
        setUserId(null)
      }
    }

    checkAuth()
  }, [pathname])

  // 🚪 Logout
  const handleLogout = async () => {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })

    setIsLoggedIn(false)
    setUserId(null)
    router.replace('/')
    router.refresh()
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 px-8 flex items-center justify-between border-b border-neutral-800 bg-black">
      <span className="text-xl font-bold">Artium</span>

      <nav className="flex items-center gap-4 text-sm text-neutral-300">
        <Link href="/" className="leading-none">
          Marketplace
        </Link>

        {!isLoggedIn ? (
          <>
            <Link
              href="/login"
              className="px-4 py-2 rounded-full bg-purple-500 text-white leading-none"
            >
              Login
            </Link>

            <Link
              href="/signup"
              className="px-4 py-2 rounded-full bg-purple-500 text-white leading-none"
            >
              Sign Up
            </Link>
          </>
        ) : (
          <>
            {userId && (
              <Link
                href={'/user/' + userId}
                className="px-4 py-2 rounded-full bg-purple-500 text-white leading-none"
              >
                Profile
              </Link>
            )}
            <button
              onClick={handleLogout}
              className="px-4 py-2 rounded-full bg-purple-500 text-white leading-none"
            >
              Logout
            </button>
          </>
        )}
      </nav>
    </header>
  )
}
