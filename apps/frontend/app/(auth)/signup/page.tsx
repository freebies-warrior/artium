import Image from 'next/image'

export default function SignupPage() {
  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
      {/* LEFT: Image */}
      <div className="relative hidden lg:block pl-8 bg-red-50">
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
          <h1 className="text-4xl font-bold mb-2">Create Account</h1>

          <p className="text-neutral-400 mb-8">
            Welcome! Enter your details and start creating, collecting and
            selling art.
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

            <input
              type="password"
              placeholder="Confirm Password"
              className="w-full px-5 py-3 rounded-full bg-white text-black placeholder-gray-500 focus:outline-none"
            />

            <button
              type="submit"
              className="w-full py-3 rounded-full bg-purple-500 hover:bg-purple-600 transition font-semibold"
            >
              Create account
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
