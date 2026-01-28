import Link from 'next/link'

export default function Navbar() {
  return (
    <header className="h-16 px-8 flex items-center justify-between border-b border-neutral-800">
      <span className="text-xl font-bold">Artium</span>

      <nav className="flex items-center gap-6 text-sm text-neutral-300">
        <Link href="/" className="leading-none">
          Marketplace
        </Link>

        <Link href="/rankings" className="leading-none">
          Rankings
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
