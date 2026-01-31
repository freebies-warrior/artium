'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'

export default function Navbar() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const router = useRouter()

  // 🔍 Check login status
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('/api/auth/me', {
          credentials: 'include',
        })
        setIsLoggedIn(res.ok)
      } catch {
        setIsLoggedIn(false)
      }
    }

    checkAuth()
  }, [])

  // 🚪 Logout
  const handleLogout = async () => {
    await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })

    setIsLoggedIn(false)
    router.replace('/')
    router.refresh()
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 px-8 flex items-center justify-between border-b border-neutral-800 bg-black">
      <Link
        href="/"
        className="flex items-center gap-2 text-xl font-bold text-white"
      >
        <Image
          src="/brand/Logo.png"
          alt="Artium logo"
          width={56}
          height={56}
          priority
        />
        <span>Artium</span>
      </Link>

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
            <Link
              href="/user"
              className="px-4 py-2 rounded-full bg-purple-500 text-white leading-none"
            >
              Profile
            </Link>
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
