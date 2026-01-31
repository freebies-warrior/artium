'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    const data = await res.json()

    setLoading(false)

    if (!res.ok) {
      setError(data?.error?.message || data?.message || 'Login failed')
      return
    }

    router.replace('/')
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      {/* LEFT: Image */}
      <div className="relative hidden lg:block">
        <Image
          src="/image.png"
          alt="Artwork"
          fill
          className="object-cover"
          priority
        />
      </div>

      {/* RIGHT: Form */}
      <div className="flex items-center justify-center px-8">
        <div className="w-full max-w-md">
          <h1 className="text-4xl font-bold mb-2">Login</h1>

          <p className="text-neutral-400 mb-8">
            Welcome back! Please enter your details.
          </p>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <input
              type="email"
              placeholder="Email Address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-5 py-3 rounded-full bg-white text-black"
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-5 py-3 rounded-full bg-white text-black"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-full bg-purple-500 hover:bg-purple-600 transition font-semibold disabled:opacity-50"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
            {error && (
              <p className="mb-4 text-red-500 text-sm text-center">{error}</p>
            )}
          </form>

          {/* Footer links */}
          <div className="mt-6 text-center text-sm text-neutral-400">
            Don’t have an account?{' '}
            <Link href="/signup" className="text-purple-400 hover:underline">
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
