'use client'

import React, { useEffect, useMemo, useState } from 'react'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'

type Img = {
  src: string
  alt?: string
}

export default function Lightbox({
  images,
  initialIndex = 0,
  isOpen,
  onClose,
}: {
  images: Img[]
  initialIndex?: number
  isOpen: boolean
  onClose: () => void
}) {
  const safeImages = useMemo(() => images?.filter(Boolean) ?? [], [images])
  const [index, setIndex] = useState(() =>
    Math.min(Math.max(0, initialIndex), safeImages.length - 1)
  )

  // Keep index in sync when opening / changing initialIndex
  useEffect(() => {
    if (!isOpen) return
    const next = Math.min(Math.max(0, initialIndex), safeImages.length - 1)
    setIndex(next)
  }, [isOpen, initialIndex, safeImages.length])

  const hasMany = safeImages.length > 1

  const goPrev = () => {
    if (!hasMany) return
    setIndex((i) => (i - 1 + safeImages.length) % safeImages.length)
  }

  const goNext = () => {
    if (!hasMany) return
    setIndex((i) => (i + 1) % safeImages.length)
  }

  // Keyboard controls + lock scroll
  useEffect(() => {
    if (!isOpen) return

    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowLeft') goPrev()
      if (e.key === 'ArrowRight') goNext()
    }

    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = prevOverflow
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, safeImages.length])

  if (!isOpen || safeImages.length === 0) return null

  const current = safeImages[index]

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80"
      onMouseDown={(e) => {
        // click outside image to close
        if (e.target === e.currentTarget) onClose()
      }}
      aria-modal="true"
      role="dialog"
    >
      <div className="relative w-full h-full flex items-center justify-center p-4">
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 inline-flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition p-2"
          aria-label="Close"
        >
          <X className="w-5 h-5 text-white" />
        </button>

        {/* Prev */}
        {hasMany && (
          <button
            onClick={goPrev}
            className="absolute left-4 md:left-6 inline-flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition p-2"
            aria-label="Previous image"
          >
            <ChevronLeft className="w-6 h-6 text-white" />
          </button>
        )}

        {/* Next */}
        {hasMany && (
          <button
            onClick={goNext}
            className="absolute right-4 md:right-6 inline-flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition p-2"
            aria-label="Next image"
          >
            <ChevronRight className="w-6 h-6 text-white" />
          </button>
        )}

        {/* Image */}
        <div className="max-w-[95vw] max-h-[85vh] select-none">
          <img
            src={current.src}
            alt={current.alt ?? `Image ${index + 1}`}
            className="max-w-[95vw] max-h-[85vh] object-contain rounded-xl"
            draggable={false}
          />
        </div>

        {/* Counter + Dots */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex flex-col items-center gap-3">
          {hasMany && (
            <div className="text-white/90 text-sm font-medium">
              {index + 1} / {safeImages.length}
            </div>
          )}

          {hasMany && (
            <div className="flex items-center gap-2">
              {safeImages.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setIndex(i)}
                  className={[
                    'h-2.5 w-2.5 rounded-full transition',
                    i === index ? 'bg-white' : 'bg-white/30 hover:bg-white/50',
                  ].join(' ')}
                  aria-label={`Go to image ${i + 1}`}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
