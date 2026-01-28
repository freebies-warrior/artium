import Image from 'next/image'
import Link from 'next/link'

export default function LoginPage() {
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

          <form className="space-y-4">
            <input
              type="email"
              placeholder="Email Address"
              className="w-full px-5 py-3 rounded-full bg-white text-black placeholder-gray-500 focus:outline-none"
            />

            <input
              type="password"
              placeholder="Password"
              className="w-full px-5 py-3 rounded-full bg-white text-black placeholder-gray-500 focus:outline-none"
            />

            <button
              type="submit"
              className="w-full py-3 rounded-full bg-purple-500 hover:bg-purple-600 transition font-semibold"
            >
              Login
            </button>
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
