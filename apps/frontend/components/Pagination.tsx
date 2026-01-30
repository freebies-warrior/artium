'use client'

type PaginationProps = {
  page: number
  hasNext?: boolean // clearer name
  onPageChange: (p: number) => void
}

export default function Pagination({
  page,
  hasNext = false,
  onPageChange,
}: PaginationProps) {
  const clamp = (p: number) => Math.max(1, p)
  const goTo = (p: number) => onPageChange(clamp(p))
  const next = () => goTo(page + 1)

  return (
    <div className="mt-8 flex flex-col items-center gap-3">
      <div className="flex items-center gap-2">
        <button
          onClick={next}
          disabled={!hasNext} // ✅ disable if no next page
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm disabled:opacity-50"
        >
          See More
        </button>
      </div>
    </div>
  )
}
