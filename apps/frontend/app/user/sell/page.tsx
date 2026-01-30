export default function SellPage() {
  return (
    <div className="min-h-screen pt-20 flex justify-center">
      <div className="w-full max-w-lg px-6">
        <h1 className="text-2xl font-bold mb-6">Add New Item</h1>

        <form className="space-y-4">
          <input
            placeholder="Title"
            className="w-full px-4 py-2 rounded bg-neutral-800"
          />
          <input
            placeholder="Price"
            className="w-full px-4 py-2 rounded bg-neutral-800"
          />
          <input type="file" className="w-full text-sm text-neutral-400" />

          <button
            type="submit"
            className="w-full py-2 rounded bg-purple-500 text-white"
          >
            Publish
          </button>
        </form>
      </div>
    </div>
  )
}
