'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { Button } from './ui/Button'
import CoordinatorReportView from './CoordinatorReport'

type AIReportButtonProps = {
  triggerText?: string
  // pass the whole features object (jsonb) or its stringified form
  features?: any
}

type Comparable = {
  id?: string
  price?: number
  title?: string
  author?: string
  location?: string
  sale_date?: string
  lot_number?: number
  similarity_score?: number
  features_preview?: string
  metadata?: any
}

function safeJsonParse(v: any): any {
  if (!v) return null
  if (typeof v === 'object') return v
  if (typeof v !== 'string') return null
  try {
    return JSON.parse(v)
  } catch {
    return null
  }
}

function fmtMoney(n?: number, currency?: string) {
  if (typeof n !== 'number') return '—'
  const cur = currency || 'SGD'
  return `${cur} ${n.toLocaleString()}`
}

function pct(sim?: number) {
  if (typeof sim !== 'number') return '—'
  return `${(sim * 100).toFixed(1)}%`
}

function getValuationObj(features: any): any {
  const obj = safeJsonParse(features)
  return obj?.valuation ?? null
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 font-mono text-lg font-semibold">{value}</div>
    </div>
  )
}

function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="rounded-xl border border-border bg-secondary/30 p-4">
      <div className="mb-3 text-sm font-semibold tracking-wide">{title}</div>
      {children}
    </div>
  )
}

function getKeySimilarities(valuation: any): string[] {
  const raw = valuation?.comparables_analysis?.key_similarities
  if (Array.isArray(raw)) return raw.filter((x) => typeof x === 'string')
  return []
}

function getMetadataResearch(valuation: any): any {
  return valuation?.metadata_research ?? null
}

function pickTopComparables(comps: Comparable[], max = 5) {
  const arr = Array.isArray(comps) ? [...comps] : []
  arr.sort((a, b) => (b.similarity_score ?? 0) - (a.similarity_score ?? 0))
  return arr.slice(0, max)
}

export default function AIReportButton({
  triggerText = 'View AI Report',
  features,
}: AIReportButtonProps) {
  const valuation = React.useMemo(() => getValuationObj(features), [features])

  const currency: string = (valuation?.currency ?? 'SGD').toString()
  const priceRange = valuation?.price_range
  const market = valuation?.market_insights

  const comparables: Comparable[] = React.useMemo(
    () => (Array.isArray(valuation?.comparables) ? valuation.comparables : []),
    [valuation]
  )

  const topComparables = React.useMemo(
    () => pickTopComparables(comparables, 5),
    [comparables]
  )

  const reasoningSteps: string[] = React.useMemo(
    () =>
      Array.isArray(valuation?.reasoning_steps) ? valuation.reasoning_steps : [],
    [valuation]
  )

  const keySimilarities = React.useMemo(
    () => getKeySimilarities(valuation),
    [valuation]
  )

  const metadataResearch = React.useMemo(
    () => getMetadataResearch(valuation),
    [valuation]
  )

  const coordinatorReport = React.useMemo(() => {
    const obj = safeJsonParse(features)
    const r1 = obj?.valuation?.coordinator_report
    const r2 = valuation?.coordinator_report
    const r = typeof r1 === 'string' && r1.trim() ? r1 : r2
    return typeof r === 'string' && r.trim() ? r : null
  }, [features, valuation])

  const hasAnything =
    !!valuation ||
    (typeof coordinatorReport === 'string' && coordinatorReport.trim().length > 0)

  const artworkType = valuation?.artwork_type ?? '—'

  const conclusion = React.useMemo(() => {
    if (
      typeof priceRange?.mid !== 'number' ||
      typeof priceRange?.low !== 'number' ||
      typeof priceRange?.high !== 'number'
    ) {
      return null
    }
    const count = comparables.length
    return `Based on comprehensive analysis of ${count} comparable artworks, market trends, and artist background, the estimated value of this artwork is ${fmtMoney(
      priceRange.mid,
      currency
    )}, with a reasonable range between ${fmtMoney(
      priceRange.low,
      currency
    )} and ${fmtMoney(priceRange.high, currency)}.`
  }, [priceRange, comparables.length, currency])

  const author = metadataResearch?.author
  const yearCreated = metadataResearch?.year_created
  const historicalPeriod = metadataResearch?.historical_period
  const artistBackground = metadataResearch?.artist_background
  const artistMarketLevel = metadataResearch?.artist_market_level
  const priceImpact = metadataResearch?.estimated_price_impact
  const researchNotes: string[] = Array.isArray(metadataResearch?.research_notes)
    ? metadataResearch.research_notes.filter((x: any) => typeof x === 'string')
    : []

  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <Button className="inline-flex items-center justify-center font-semibold rounded-xl transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ring-offset-background disabled:opacity-50 disabled:pointer-events-none cursor-pointer bg-purple-600 text-white hover:bg-purple-700 active:scale-[0.99] h-12 px-8 text-base w-full">
          {triggerText}
        </Button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />

        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-3xl -translate-x-1/2 -translate-y-1/2 grid gap-4
                     border border-border bg-neutral-800 p-6 shadow-lg
                     data-[state=open]:animate-in data-[state=closed]:animate-out
                     data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
                     data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95
                     data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]
                     data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]
                     sm:rounded-lg"
        >
          <div className="flex flex-col space-y-1.5 text-center sm:text-left">
            <Dialog.Title className="tracking-tight text-xl font-bold">
              AI Valuation Report
            </Dialog.Title>
            <Dialog.Description className="text-sm text-muted-foreground">
              Structured view from <span className="font-mono">features.valuation</span>.
            </Dialog.Description>
          </div>

          {!hasAnything ? (
            <div className="rounded-lg border border-border bg-background/40 p-4">
              <p className="text-sm text-muted-foreground">
                The Agents is in the middle of evaluating, please comeback again later
              </p>
            </div>
          ) : (
            <div className="max-h-[70vh] overflow-auto pr-1 space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <StatCard
                  label="Most Likely"
                  value={fmtMoney(priceRange?.mid, currency)}
                />
                <StatCard
                  label="Low / High"
                  value={
                    typeof priceRange?.low === 'number' &&
                    typeof priceRange?.high === 'number'
                      ? `${fmtMoney(priceRange.low, currency)} – ${fmtMoney(
                          priceRange.high,
                          currency
                        )}`
                      : '—'
                  }
                />
                <StatCard label="Artwork Type" value={String(artworkType)} />
              </div>

              {/* Conclusion under summary cards */}
              {conclusion && (
                <div className="rounded-xl border border-border bg-background/40 p-4">
                  <div className="text-xs font-semibold text-muted-foreground mb-1">
                    Conclusion
                  </div>
                  <p className="text-sm leading-relaxed text-foreground/90">
                    {conclusion}
                  </p>
                </div>
              )}

              {/* Market */}
              <Section title="Market Analysis">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  <StatCard
                    label="Avg Price"
                    value={fmtMoney(market?.avg_price, currency)}
                  />
                  <StatCard
                    label="Median Price"
                    value={fmtMoney(market?.median_price, currency)}
                  />
                  <StatCard
                    label="Trend"
                    value={(market?.trend_direction ?? '—').toString()}
                  />
                  <StatCard
                    label="Recent Sales (12mo)"
                    value={
                      typeof market?.num_recent_sales === 'number'
                        ? `${market.num_recent_sales}`
                        : '—'
                    }
                  />
                </div>
              </Section>

              {/* Comparable Artworks */}
              <Section title={`Comparable Artworks (Top ${topComparables.length})`}>
                {topComparables.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No comparables.</p>
                ) : (
                  <div className="space-y-3">
                    {topComparables.map((c, idx) => (
                      <div
                        key={c.id ?? `${idx}-${c.title ?? 'comp'}`}
                        className="rounded-xl border border-border bg-card p-4"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                          <div>
                            <div className="text-sm font-semibold">
                              {idx + 1}. {c.title ?? 'Untitled'}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {c.author ?? 'Unknown'}
                              {c.location ? ` • ${c.location}` : ''}
                              {c.sale_date ? ` • ${c.sale_date}` : ''}
                              {typeof c.lot_number === 'number'
                                ? ` • Lot ${c.lot_number}`
                                : ''}
                            </div>
                          </div>

                          <div className="flex gap-2">
                            <div className="rounded-lg bg-secondary/40 px-3 py-2">
                              <div className="text-[10px] text-muted-foreground">
                                Price
                              </div>
                              <div className="font-mono text-sm">
                                {fmtMoney(c.price, currency)}
                              </div>
                            </div>
                            <div className="rounded-lg bg-secondary/40 px-3 py-2">
                              <div className="text-[10px] text-muted-foreground">
                                Similarity
                              </div>
                              <div className="font-mono text-sm">
                                {pct(c.similarity_score)}
                              </div>
                            </div>
                          </div>
                        </div>

                        {c.features_preview && (
                          <details className="mt-3">
                            <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground">
                              Show features preview
                            </summary>
                            <pre className="mt-2 whitespace-pre-wrap text-xs text-muted-foreground leading-relaxed">
                              {c.features_preview}
                            </pre>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </Section>

              {/* Key Similarities */}
              <Section title="Key Similarities to Comparables">
                {keySimilarities.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No key similarities found.
                  </p>
                ) : (
                  <ul className="list-disc pl-5 space-y-2 text-sm text-foreground/90">
                    {keySimilarities.slice(0, 8).map((s, i) => (
                      <li key={i} className="whitespace-pre-wrap">
                        {s}
                      </li>
                    ))}
                  </ul>
                )}
              </Section>

              {/* Artist & Historical Background */}
              <Section title="Artist & Historical Background">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <StatCard label="Artist" value={author ? String(author) : '—'} />
                  <StatCard
                    label="Year Created"
                    value={
                      typeof yearCreated === 'number' ||
                      typeof yearCreated === 'string'
                        ? String(yearCreated)
                        : '—'
                    }
                  />
                  <StatCard
                    label="Historical Period"
                    value={historicalPeriod ? String(historicalPeriod) : '—'}
                  />
                </div>

                {(artistMarketLevel || priceImpact) && (
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                    <StatCard
                      label="Market Level"
                      value={artistMarketLevel ? String(artistMarketLevel) : '—'}
                    />
                    <StatCard
                      label="Price Impact"
                      value={priceImpact ? String(priceImpact) : '—'}
                    />
                  </div>
                )}

                {artistBackground && (
                  <div className="mt-3 rounded-lg border border-border bg-background/40 p-4">
                    <div className="text-xs font-semibold text-muted-foreground">
                      Artist Background
                    </div>
                    <div className="mt-2 text-sm whitespace-pre-wrap text-foreground/90">
                      {String(artistBackground)}
                    </div>
                  </div>
                )}

                {researchNotes.length > 0 && (
                  <div className="mt-3 rounded-lg border border-border bg-background/40 p-4">
                    <div className="text-xs font-semibold text-muted-foreground">
                      Research Notes
                    </div>
                    <ul className="mt-2 list-disc pl-5 space-y-1 text-sm text-foreground/90">
                      {researchNotes.slice(0, 10).map((n, i) => (
                        <li key={i} className="whitespace-pre-wrap">
                          {n}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </Section>

              {/* Methodology */}
              <Section title="Valuation Methodology">
                {reasoningSteps.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No steps.</p>
                ) : (
                  <ol className="list-decimal pl-5 space-y-2 text-sm text-foreground/90">
                    {reasoningSteps.map((s, i) => (
                      <li key={i} className="whitespace-pre-wrap">
                        {s}
                      </li>
                    ))}
                  </ol>
                )}
              </Section>

              {/* Coordinator Report */}
              <Section title="Coordinator Report">
                {coordinatorReport ? (
                  <CoordinatorReportView report={coordinatorReport} />
                ) : (
                  <p className="text-sm text-muted-foreground">
                    The Agents is in the middle of evaluating, please comeback again later
                  </p>
                )}
              </Section>
            </div>
          )}

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
