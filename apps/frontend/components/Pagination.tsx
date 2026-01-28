"use client";

type PaginationProps = {
  page: number;
  totalItems: number;
  pageSize?: number;
  onPageChange: (p: number) => void;
};

export default function Pagination({
  page,
  totalItems,
  pageSize = 12,
  onPageChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  const clamp = (p: number) => Math.min(totalPages, Math.max(1, p));
  const goTo = (p: number) => onPageChange(clamp(p));
  const prev = () => goTo(page - 1);
  const next = () => goTo(page + 1);

  const pagesToShow = getPages(page, totalPages);

  return (
    <div className="mt-8 flex flex-col items-center gap-3">
      <div className="flex items-center gap-2">
        <button
          onClick={prev}
          disabled={page === 1}
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm disabled:opacity-50"
        >
          Prev
        </button>

        <div className="flex items-center gap-1">
          {pagesToShow.map((p, i) =>
            p === "..." ? (
              <span key={`dots-${i}`} className="px-2 text-muted-foreground">
                ...
              </span>
            ) : (
              <button
                key={p}
                onClick={() => goTo(p)}
                className={[
                  "h-9 min-w-9 rounded-lg border px-3 text-sm",
                  p === page
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-card hover:bg-muted",
                ].join(" ")}
              >
                {p}
              </button>
            )
          )}
        </div>

        <button
          onClick={next}
          disabled={page === totalPages}
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm disabled:opacity-50"
        >
          Next
        </button>
      </div>

      <p className="text-sm text-muted-foreground">
        Page <span className="font-medium text-foreground">{page}</span> of{" "}
        <span className="font-medium text-foreground">{totalPages}</span>
      </p>
    </div>
  );
}

function getPages(current: number, total: number): Array<number | "..."> {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

  const pages: Array<number | "..."> = [];
  pages.push(1);

  const left = Math.max(2, current - 1);
  const right = Math.min(total - 1, current + 1);

  if (left > 2) pages.push("...");

  for (let p = left; p <= right; p++) pages.push(p);

  if (right < total - 1) pages.push("...");

  pages.push(total);
  return pages;
}
