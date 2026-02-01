import Link from 'next/link'

export default function AddItemButton() {
  return (
    <Link
      href={`/users/sell`}
      className="px-4 py-2 rounded-full bg-purple-500 text-white font-medium"
    >
      + Add Item
    </Link>
  )
}
