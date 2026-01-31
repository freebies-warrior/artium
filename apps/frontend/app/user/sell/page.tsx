'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'

const MAX_IMAGES = 10

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

  // Multiple images
  const [imageFiles, setImageFiles] = useState<File[]>([])
  const [imagePreviews, setImagePreviews] = useState<string[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)

  // Keep track of previews for cleanup
  const previewsRef = useRef<string[]>([])
  useEffect(() => {
    return () => {
      previewsRef.current.forEach((url) => URL.revokeObjectURL(url))
    }
  }, [])

  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function replaceImages(newFiles: File[]) {
    // Revoke old previews
    previewsRef.current.forEach((url) => URL.revokeObjectURL(url))

    const newPreviews = newFiles.map((f) => URL.createObjectURL(f))
    previewsRef.current = newPreviews

    setImageFiles(newFiles)
    setImagePreviews(newPreviews)
    setSelectedIndex(0)
  }

  function addImages(filesToAdd: File[]) {
    const combined = [...imageFiles, ...filesToAdd]
    const trimmed = combined.slice(0, MAX_IMAGES)
    replaceImages(trimmed)

    if (combined.length > MAX_IMAGES) {
      setError(`You can upload up to ${MAX_IMAGES} images. Extra images were ignored.`)
    }
  }

  function removeImage(idx: number) {
    const nextFiles = imageFiles.filter((_, i) => i !== idx)
    replaceImages(nextFiles)

    // Adjust selection
    setSelectedIndex((prev) => {
      if (nextFiles.length === 0) return 0
      if (prev === idx) return 0
      if (prev > idx) return prev - 1
      return prev
    })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (!timeStart || !timeEnd) {
      setError('Please select start and end time')
      return
    }

    if (imageFiles.length === 0) {
      setError('Please upload at least one artwork image')
      return
    }

    if (imageFiles.length > MAX_IMAGES) {
      setError(`You can upload up to ${MAX_IMAGES} images`)
      return
    }

    setLoading(true)

    try {
      // Upload all images (sequentially; simpler and easier to debug)
      const keys: string[] = []

      for (let i = 0; i < imageFiles.length; i++) {
        const file = imageFiles[i]

        const presignRes = await fetch('/api/uploads/presign', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            filename: file.name,
            content_type: file.type,
          }),
        })

        const text = await presignRes.text()
        const presignData = text ? JSON.parse(text) : null

        if (!presignRes.ok) {
          throw new Error(
            presignData?.message || `Failed to get upload URL (image ${i + 1})`
          )
        }

        const { upload_url, key } = presignData as { upload_url: string; key: string }

        const putRes = await fetch(upload_url, {
          method: 'PUT',
          headers: {
            'Content-Type': file.type,
          },
          body: file,
        })

        if (!putRes.ok) {
          throw new Error(`Failed to upload image ${i + 1}`)
        }

        keys.push(key)
      }

      // Create item with all picture keys
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
          picture_keys: keys,
        }),
      })

      const data = await res.json()
      setLoading(false)

      if (res.ok && (data.item || data.id)) {
        const itemId = data.item?.id ?? data.id
        router.push(`/art/${itemId}`)
        return
      }

      setError(data?.error?.message || 'Request failed')
    } catch (err: any) {
      setLoading(false)
      setError(err?.message || 'Request failed')
    }
  }

  const selectedPreview = imagePreviews[selectedIndex] ?? null

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
              Fields marked with <span className="text-red-500">*</span> are required
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
            <div className="space-y-4">
              <label className="block mb-2 text-xs text-neutral-400">
                Artwork Images <span className="text-red-500">*</span>{' '}
                <span className="text-neutral-500">(max {MAX_IMAGES})</span>
              </label>

              <div className="space-y-3">
                {/* Main preview */}
                <div className="relative h-100 rounded-lg border border-neutral-700 bg-neutral-900 overflow-hidden">
                  {selectedPreview ? (
                    <Image
                      src={selectedPreview}
                      alt="Artwork preview"
                      fill
                      className="object-contain"
                      unoptimized
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-neutral-500 text-sm">
                      Image Preview
                    </div>
                  )}
                </div>

                {/* Thumbnails */}
                {imagePreviews.length > 0 && (
                  <div className="grid grid-cols-5 gap-2">
                    {imagePreviews.map((src, idx) => (
                      <div
                        key={src}
                        className={`relative aspect-square overflow-hidden rounded border ${
                          idx === selectedIndex
                            ? 'border-purple-500'
                            : 'border-neutral-700'
                        } bg-neutral-900`}
                      >
                        <button
                          type="button"
                          onClick={() => setSelectedIndex(idx)}
                          className="absolute inset-0 z-10"
                          aria-label={`Select image ${idx + 1}`}
                        />
                        <Image
                          src={src}
                          alt={`Preview ${idx + 1}`}
                          fill
                          className="object-cover"
                          unoptimized
                        />
                        <button
                          type="button"
                          onClick={() => removeImage(idx)}
                          className="absolute top-1 right-1 z-20 rounded bg-black/60 px-2 py-1 text-xs text-white hover:bg-black/80"
                          aria-label={`Remove image ${idx + 1}`}
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* File input */}
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  className="w-full text-sm text-neutral-400"
                  onChange={(e) => {
                    setError(null)

                    const files = Array.from(e.target.files ?? [])
                      .filter((f) => f.type.startsWith('image/'))

                    if (files.length === 0) return

                    // Enforce max total (allow adding in multiple selections)
                    if (imageFiles.length >= MAX_IMAGES) {
                      setError(`You already selected ${MAX_IMAGES} images (max).`)
                      e.target.value = ''
                      return
                    }

                    const remaining = MAX_IMAGES - imageFiles.length
                    const toAdd = files.slice(0, remaining)
                    addImages(toAdd)

                    // Allow selecting the same file again later
                    e.target.value = ''
                  }}
                />

                <div className="text-xs text-neutral-500">
                  Selected: {imageFiles.length}/{MAX_IMAGES}
                </div>
              </div>
            </div>

            <button
              type="submit"
              form="sell-form"
              disabled={loading}
              className="mt-auto w-full py-3 rounded bg-purple-500 text-white text-lg font-medium disabled:opacity-50"
            >
              {loading ? 'Publishing…' : 'Publish'}
            </button>

            {error && (
              <div className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-400">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
