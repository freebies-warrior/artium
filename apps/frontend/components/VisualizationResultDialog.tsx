'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X, Loader2, ImageOff } from 'lucide-react'
import { Button } from './ui/Button'

type VisualizationJob = {
  id: string
  status: 'queued' | 'processing' | 'succeeded' | 'failed'
  result_image_url?: string | null
  result_description?: string | null
  error_message?: string | null
}

type VisualizationResultDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  job: VisualizationJob | null
}

export default function VisualizationResultDialog({
  open,
  onOpenChange,
  job,
}: VisualizationResultDialogProps) {
  const status = job?.status

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        {/* Overlay */}
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm" />

        {/* Content */}
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl -translate-x-1/2 -translate-y-1/2
                     rounded-xl border border-border bg-neutral-900 p-6 shadow-xl"
        >
          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <Dialog.Title className="text-xl font-bold">
                Preview in your space
              </Dialog.Title>
              <Dialog.Description className="text-sm text-muted-foreground">
                AI-generated visualization
              </Dialog.Description>
            </div>

            <Dialog.Close asChild>
              <button
                aria-label="Close"
                className="rounded-md p-1 opacity-70 hover:opacity-100"
              >
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Body */}
          <div className="mt-6">
            {/* LOADING / PROCESSING */}
            {(status === 'queued' || status === 'processing') && (
              <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <div className="text-base font-medium">
                  Generating preview…
                </div>
                <p className="max-w-sm text-sm text-muted-foreground">
                  This usually takes a few seconds. Please keep this window
                  open.
                </p>
              </div>
            )}

            {/* SUCCEEDED */}
            {status === 'succeeded' && (
              <div className="space-y-6">
                {job?.result_image_url ? (
                  <div className="overflow-hidden rounded-lg border border-border">
                    <img
                      src={job.result_image_url}
                      alt="Visualization result"
                      className="w-full object-contain"
                    />
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2 rounded-lg border border-dashed border-border py-12 text-muted-foreground">
                    <ImageOff className="h-5 w-5" />
                    Result image not available
                  </div>
                )}

                {job?.result_description && (
                  <div className="rounded-lg bg-secondary/40 p-4">
                    <h4 className="mb-1 text-sm font-semibold">
                      AI Description
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      {job.result_description}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* FAILED */}
            {status === 'failed' && (
              <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
                <div className="text-lg font-semibold text-destructive">
                  Visualization failed
                </div>
                <p className="max-w-md text-sm text-muted-foreground">
                  {job?.error_message ??
                    'Something went wrong while generating the preview.'}
                </p>
                <Button onClick={() => onOpenChange(false)}>
                  Close
                </Button>
              </div>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
