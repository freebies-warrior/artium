import Link from 'next/link'

export default function AddItemButton({ userId }: { userId: string }) {
  return (
    <Link
      href={`/users/${userId}/sell`}
      className="px-4 py-2 rounded-full bg-purple-500 text-white font-medium"
    >
      + Add Item
    </Link>
  )
}
