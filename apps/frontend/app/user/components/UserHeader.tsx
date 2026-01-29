import AddItemButton from './AddItemButton'

export default function UserHeader() {
  return (
    <div className="flex items-center gap-6 mb-8">
      <div className="h-24 w-24 rounded-full bg-neutral-700" />

      <div className="flex-1">
        <h1 className="text-2xl font-bold">Your Profile</h1>
        <p className="text-neutral-400">Manage your listings</p>
      </div>

      <AddItemButton />
    </div>
  )
}
