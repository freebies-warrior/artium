'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { Button } from './ui/Button'

type PreviewButtonProps = {
  itemName?: string
  triggerText?: string
  onSubmit?: (file: File) => void // optional hook for later
}

export default function PreviewButton({
  itemName,
  triggerText = 'View in your space',
  onSubmit,
}: PreviewButtonProps) {
  const [file, setFile] = React.useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = React.useState<string | null>(null)

  const canSubmit = !!file

  function pickFile(next: File | null) {
    if (!next) return

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

  function handleSubmit() {
    if (!file) return

    // Placeholder logic; replace later with your upload/generation call
    console.log('Submit room photo for:', itemName, file)

    onSubmit?.(file)
  }

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  return (
    <Dialog.Root
      onOpenChange={(open) => {
        // optional: reset state when closing
        if (!open) {
          // keep selection if you want; if you prefer reset on close, uncomment:
          // clearFile();
        }
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
                    PNG / JPG • 1 photo only
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

            {/* Submit */}
            <Button fullWidth disabled={!canSubmit} onClick={handleSubmit}>
              Submit Photo
            </Button>
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
  )
}
