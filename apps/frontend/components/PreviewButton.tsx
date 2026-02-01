'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { Button } from './ui/Button'
import VisualizationResultDialog from './VisualizationResultDialog'

const MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024 // 1MB
const MAX_FILE_SIZE_BYTES_STRING = '1MB'

type VisualizationJob = {
  id: string
  status: 'queued' | 'processing' | 'succeeded' | 'failed'
  result_image_url?: string | null
  result_description?: string | null
  error_message?: string | null
}

type PreviewButtonProps = {
  itemName?: string
  triggerText?: string

  // REQUIRED for the workflow
  itemId: string
  itemImageKey: string

  // optional; if not provided we send nulls
  itemWidthCm?: number
  itemHeightCm?: number
}

export default function PreviewButton({
  itemName,
  triggerText = 'View in your space',
  itemId,
  itemImageKey,
  itemWidthCm,
  itemHeightCm,
}: PreviewButtonProps) {
  // upload state (same pattern as SellPage)
  const [file, setFile] = React.useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = React.useState<string | null>(null)

  // UI state
  const [error, setError] = React.useState<string | null>(null)
  const [submitting, setSubmitting] = React.useState(false)

  // result dialog state
  const [resultOpen, setResultOpen] = React.useState(false)
  const [job, setJob] = React.useState<VisualizationJob | null>(null)

  const canSubmit = !!file && !submitting

  function pickFile(next: File | null) {
    if (!next) return

    setError(null)

    // ✅ size limit: 1MB
    if (next.size > MAX_FILE_SIZE_BYTES) {
      setError(`File too large. Max ${MAX_FILE_SIZE_BYTES_STRING}.`)
      return
    }

    // ✅ Only 1 photo allowed: replace existing
    setFile(next)

    const url = URL.createObjectURL(next)
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return url
    })
  }

  function clearFile() {
    setFile(null)
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return null
    })
  }

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  // Polling: when dialog is open and job is queued/processing
  React.useEffect(() => {
    if (!resultOpen) return
    if (!job?.id) return
    if (job.status === 'succeeded' || job.status === 'failed') return

    let stopped = false
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/visualization?job_id=${job.id}`, {
          method: 'GET',
          cache: 'no-store',
        })
        const data = await res.json()

        if (!res.ok) {
          // if backend returns error shape
          const msg = data?.error?.message || data?.message || 'Polling failed'
          if (!stopped) {
            setJob((prev) =>
<<<<<<< HEAD
              prev ? { ...prev, status: 'failed', error_message: msg } : prev
=======
              prev
                ? { ...prev, status: 'failed', error_message: msg }
                : prev
>>>>>>> 9b24712 (Integrate Preview Button)
            )
          }
          return
        }

        const nextJob = data?.job as VisualizationJob | undefined
        if (!nextJob) return

        if (!stopped) setJob(nextJob)
      } catch (e: any) {
        if (!stopped) {
          setJob((prev) =>
            prev
              ? {
                  ...prev,
                  status: 'failed',
                  error_message: e?.message || 'Polling failed',
                }
              : prev
          )
        }
      }
    }, 2000)

    return () => {
      stopped = true
      clearInterval(interval)
    }
  }, [resultOpen, job?.id, job?.status])

  async function handleSubmit() {
    if (!file) return
    setError(null)
    setSubmitting(true)

    try {
      // 1) Presign upload for room image
      const presignRes = await fetch('/api/uploads/presign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type,
        }),
      })

      const presignText = await presignRes.text()
      const presignData = presignText ? JSON.parse(presignText) : null

      if (!presignRes.ok) {
        throw new Error(
          presignData?.error?.message ||
            presignData?.message ||
            'Failed to get upload URL'
        )
      }

      const { upload_url, key: room_image_key } = presignData as {
        upload_url: string
        key: string
      }

      // 2) Upload room image directly to R2 (PUT)
      const putRes = await fetch(upload_url, {
        method: 'PUT',
        headers: {
          'Content-Type': file.type,
        },
        body: file,
      })

      if (!putRes.ok) {
        throw new Error('Failed to upload room image')
      }

      // 3) Create visualization job
      const createRes = await fetch('/api/visualization', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_id: itemId,
          item_image_key: itemImageKey,
          room_image_key,
          item_dimensions:
            itemWidthCm && itemHeightCm
              ? { width_cm: itemWidthCm, height_cm: itemHeightCm }
              : null,
        }),
      })

      const createData = await createRes.json()

      if (!createRes.ok) {
        throw new Error(
          createData?.error?.message ||
            createData?.message ||
            'Failed to create visualization job'
        )
      }

      const createdJob = createData?.job as VisualizationJob | undefined
      if (!createdJob?.id) {
        throw new Error('Invalid job response from backend')
      }

      // 4) Open result dialog + start polling
      setJob(createdJob)
      setResultOpen(true)
      setSubmitting(false)
    } catch (err: any) {
      setSubmitting(false)
      setError(err?.message || 'Request failed')
    }
  }

  return (
    <>
      {/* Result dialog */}
      <VisualizationResultDialog
        open={resultOpen}
        onOpenChange={(open) => {
          setResultOpen(open)
          // Optional: reset job when closing
          // if (!open) setJob(null)
        }}
        job={job}
      />

      {/* Upload dialog */}
      <Dialog.Root
        onOpenChange={(open) => {
          // optional: reset errors when closing
          if (!open) setError(null)
        }}
      >
        <Dialog.Trigger asChild>
          <Button className="inline-flex items-center justify-center font-semibold rounded-xl transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background disabled:opacity-50 disabled:pointer-events-none cursor-pointer bg-purple-600 text-white hover:bg-purple-700 active:scale-[0.99] h-12 px-8 text-base w-full">
            {triggerText}
          </Button>
        </Dialog.Trigger>

        <Dialog.Portal>
          {/* Overlay */}
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />

          {/* Content */}
          <Dialog.Content
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 grid gap-4
                     border border-border bg-neutral-800 p-6 shadow-lg
                     data-[state=open]:animate-in data-[state=closed]:animate-out
                     data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
                     data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95
                     data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]
                     data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]
                     sm:rounded-lg sm:max-w-md"
          >
            {/* Header */}
            <div className="bg-neutral-850 flex flex-col space-y-1.5 text-center sm:text-left">
              <Dialog.Title className="tracking-tight text-xl font-bold">
                Preview in your space
              </Dialog.Title>
              <Dialog.Description className="text-sm text-muted-foreground">
                Upload 1 photo of your room to preview{' '}
                <span className="text-primary font-medium">{itemName}</span>.
                <span className="ml-1 text-xs text-neutral-400">
                  (Max {MAX_FILE_SIZE_BYTES_STRING})
                </span>
              </Dialog.Description>
            </div>

            {/* Body */}
            <div className="space-y-6 py-4">
              {/* Upload box */}
              <div className="rounded-lg bg-secondary/50 p-4">
                <input
                  id="room-photo"
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
                />

                {!previewUrl ? (
                  <label
                    htmlFor="room-photo"
                    className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-background/40 px-4 py-8 text-center hover:bg-muted transition"
                  >
                    <div className="text-sm font-medium">
                      Click to upload a room photo
                    </div>
                    <div className="text-xs text-muted-foreground">
<<<<<<< HEAD
                      PNG / JPG • 1 photo only • Max{' '}
                      {MAX_FILE_SIZE_BYTES_STRING}
=======
                      PNG / JPG • 1 photo only • Max {MAX_FILE_SIZE_BYTES_STRING}
>>>>>>> 9b24712 (Integrate Preview Button)
                    </div>
                  </label>
                ) : (
                  <div className="space-y-3">
                    <div className="overflow-hidden rounded-lg border border-border">
                      <img
                        src={previewUrl}
                        alt="Room photo preview"
                        className="h-56 w-full object-cover"
                      />
                    </div>

                    <div className="flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between">
                      <p className="text-xs text-muted-foreground">
                        Selected:{' '}
                        <span className="text-foreground">{file?.name}</span>
                      </p>

                      <div className="flex gap-2">
                        <label
                          htmlFor="room-photo"
                          className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-border bg-card px-3 py-2 text-sm hover:bg-muted transition"
                        >
                          Replace
                        </label>
                        <button
                          type="button"
                          onClick={clearFile}
                          className="inline-flex items-center justify-center rounded-lg border border-border bg-card px-3 py-2 text-sm hover:bg-muted transition"
                        >
                          Remove
                        </button>
                      </div>
                    </div>

                    <p className="text-xs text-muted-foreground">
                      Tip: Use a well-lit photo with a clear wall for best
                      results.
                    </p>
                  </div>
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-md border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-400">
                  {error}
                </div>
              )}

              {/* Submit */}
              <Button fullWidth disabled={!canSubmit} onClick={handleSubmit}>
                {submitting ? 'Submitting…' : 'Submit Photo'}
              </Button>

              {/* Optional: Open results if already created */}
              {job?.id && (
                <button
                  type="button"
                  className="w-full text-xs text-neutral-400 hover:text-white transition"
                  onClick={() => setResultOpen(true)}
                >
                  View last preview result
                </button>
              )}
            </div>

            {/* Close */}
            <Dialog.Close asChild>
              <button
                type="button"
                className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity
                         hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2
                         disabled:pointer-events-none"
                aria-label="Close"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Close</span>
              </button>
            </Dialog.Close>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  )
}
