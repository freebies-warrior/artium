'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'

export default function SellPage() {
  const router = useRouter()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [author, setAuthor] = useState('')
  const [basePrice, setBasePrice] = useState('0')
  const [increment, setIncrement] = useState('1')
  const [yearCreated, setYearCreated] = useState('')
  const [height, setHeight] = useState('')
  const [width, setWidth] = useState('')
  const [timeStart, setTimeStart] = useState('')
  const [timeEnd, setTimeEnd] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)

  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!timeStart || !timeEnd) {
      setError('Please select start and end time')
      return
    }

    if (!imageFile) {
      setError('Please upload an artwork image')
      return
    }

    setLoading(true)

    const presignRes = await fetch('/api/uploads/presign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: imageFile.name,
        content_type: imageFile.type,
      }),
    })

    const text = await presignRes.text()
    const presignData = text ? JSON.parse(text) : null

    if (!presignRes.ok) {
      setError(presignData?.message || 'Failed to get upload URL')
      setLoading(false)
      return
    }

    const { upload_url, key } = presignData

    const putRes = await fetch(upload_url, {
      method: 'PUT',
      headers: {
        'Content-Type': imageFile.type,
      },
      body: imageFile,
    })

    if (!putRes.ok) {
      setError('Failed to upload image')
      setLoading(false)
      return
    }

    const res = await fetch('/api/items', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title,
        description: description || null,
        author: author || null,
        base_price: Number(basePrice),
        increment: Number(increment),
        year_created: yearCreated ? Number(yearCreated) : null,
        height: height ? Number(height) : null,
        width: width ? Number(width) : null,
        time_start: new Date(timeStart).toISOString(),
        time_end: new Date(timeEnd).toISOString(),
        picture_keys: [key],
      }),
    })

    const data = await res.json()
    console.log(data)
    setLoading(false)

    if (res.ok && (data.item || data.id)) {
      const itemId = data.item?.id ?? data.id
      router.push(`/art/${itemId}`)
      return
    }

    setError(data?.error?.message || 'Request failed')
  }

  return (
    <div className="min-h-screen pt-20 flex justify-center">
      <div className="w-full max-w-5xl px-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Add An Item to the Auction</h1>

          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition"
          >
            ← Back
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* LEFT COLUMN — FORM */}
          <div>
            <p className="mb-4 text-sm text-neutral-400">
              Fields marked with <span className="text-red-500">*</span> are
              required
            </p>

            <form id="sell-form" onSubmit={handleSubmit} className="space-y-4">
              {/* Title */}
              <div>
                <label className="block mb-1 text-xs text-neutral-400">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Prices */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1 text-xs text-neutral-400">
                    Base Price{' '}
                    <span className="text-neutral-500">(default: 0)</span>
                  </label>
                  <input
                    type="number"
                    value={basePrice}
                    onChange={(e) => setBasePrice(e.target.value)}
                    className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block mb-1 text-xs text-neutral-400">
                    Minimum Increment <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    value={increment}
                    onChange={(e) => setIncrement(e.target.value)}
                    className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              {/* Time */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1 text-xs text-neutral-400">
                    Start Time <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={timeStart}
                    onChange={(e) => setTimeStart(e.target.value)}
                    className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none"
                    style={{ colorScheme: 'dark' }}
                  />
                </div>

                <div>
                  <label className="block mb-1 text-xs text-neutral-400">
                    End Time <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="datetime-local"
                    value={timeEnd}
                    onChange={(e) => setTimeEnd(e.target.value)}
                    className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none"
                    style={{ colorScheme: 'dark' }}
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block mb-1 text-xs text-neutral-400">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Author + Year */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1 text-xs text-neutral-400">
                    Author
                  </label>
                  <input
                    value={author}
                    onChange={(e) => setAuthor(e.target.value)}
                    className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block mb-1 text-xs text-neutral-400">
                    Year Created
                  </label>
                  <input
                    type="number"
                    value={yearCreated}
                    onChange={(e) => setYearCreated(e.target.value)}
                    className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              {/* Dimensions */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block mb-1 text-xs text-neutral-400">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                    className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div>
                  <label className="block mb-1 text-xs text-neutral-400">
                    Width (cm)
                  </label>
                  <input
                    type="number"
                    value={width}
                    onChange={(e) => setWidth(e.target.value)}
                    className="w-full px-4 py-2 rounded bg-neutral-800 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>
            </form>
          </div>

          {/* RIGHT COLUMN — IMAGE + SUBMIT */}
          <div className="flex flex-col h-full">
            {/* Top content */}
            <div className="space-y-4">
              <label className="block mb-2 text-xs text-neutral-400">
                Artwork Image <span className="text-red-500">*</span>
              </label>

              <div className="space-y-3">
                <div className="relative h-100 rounded-lg border border-neutral-700 bg-neutral-900 overflow-hidden">
                  {imagePreview ? (
                    <Image
                      src={imagePreview}
                      alt="Artwork preview"
                      fill
                      className="object-contain"
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-neutral-500 text-sm">
                      Image Preview
                    </div>
                  )}
                </div>

                <input
                  type="file"
                  accept="image/*"
                  className="w-full text-sm text-neutral-400"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (!file) return
                    setImageFile(file)
                    setImagePreview(URL.createObjectURL(file))
                  }}
                />
              </div>
            </div>

            {/* Push button to bottom */}
            <button
              type="submit"
              form="sell-form"
              disabled={loading}
              className="mt-auto w-full py-3 rounded bg-purple-500 text-white text-lg font-medium disabled:opacity-50"
            >
              {loading ? 'Publishing…' : 'Publish'}
            </button>
            {error && (
              <div className="mb-4 rounded-md border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-400">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
