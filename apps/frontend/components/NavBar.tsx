import Link from 'next/link'

export default function Navbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 px-8 flex items-center justify-between border-b border-neutral-800 bg-black">
      <span className="text-xl font-bold">Artium</span>

      <nav className="flex items-center gap-6 text-sm text-neutral-300">
        <Link href="/" className="leading-none">
          Marketplace
        </Link>

        <Link
          href="/signup"
          className="px-4 py-2 rounded-full bg-purple-500 text-white leading-none"
        >
          Sign Up
        </Link>
      </nav>
    </header>
  )
}
