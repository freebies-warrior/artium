'use client'

import { useState } from 'react'
import Image from 'next/image'

export default function SignupPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    if (password !== confirmPassword) {
      setLoading(false)
      setError('Passwords do not match')
      return
    }

    const res = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    })

    const data = await res.json()
    setLoading(false)

    if (!res.ok) {
      setError(data?.error?.message || data?.message || 'Signup failed')
      return
    }

    setSuccess(
      'Account created! Please check your email to verify your account.'
    )
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      {/* LEFT */}
      <div className="relative hidden lg:block pl-8 bg-red-50">
        <Image
          src="/image.png"
          alt="Artwork"
          fill
          className="object-cover"
          priority
        />
      </div>

      {/* RIGHT */}
      <div className="flex items-center justify-center px-8">
        <div className="w-full max-w-md">
          <h1 className="text-4xl font-bold mb-2">Create Account</h1>

          <p className="text-neutral-400 mb-8">
            Welcome! Enter your details and start creating, collecting and
            selling art.
          </p>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <input
              type="username"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-5 py-3 rounded-full bg-white text-black"
            />

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

            <input
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-5 py-3 rounded-full bg-white text-black"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-full bg-purple-500 hover:bg-purple-600 transition font-semibold disabled:opacity-50"
            >
              {loading ? 'Creating account...' : 'Create account'}
            </button>

            {error && (
              <p className="mb-4 text-red-500 text-sm text-center">{error}</p>
            )}

            {success && (
              <p className="mb-4 text-green-500 text-sm text-center">
                {success}
              </p>
            )}
          </form>
        </div>
      </div>
    </div>
  )
}
