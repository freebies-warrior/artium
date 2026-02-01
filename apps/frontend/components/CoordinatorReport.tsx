'use client'

import * as React from 'react'

type Props = {
  report: string
}

type Block =
  | { type: 'h1'; text: string; underline: boolean }
  | { type: 'h2'; text: string; underline: boolean }
  | { type: 'p'; text: string }
  | { type: 'ul'; items: string[] }
  | { type: 'ol'; items: string[] }
  | { type: 'spacer' }

function isRuleLine(s: string) {
  const t = s.trim()
  if (!t) return false
  // matches "======" or "------"
  return /^[=-]{6,}$/.test(t)
}

function isEqualsRule(s: string) {
  const t = s.trim()
  return /^={6,}$/.test(t)
}

function isDashesRule(s: string) {
  const t = s.trim()
  return /^-{6,}$/.test(t)
}

function isAllCapsTitle(s: string) {
  const t = s.trim()
  if (!t) return false
  if (!/^[A-Z0-9 &]+$/.test(t)) return false
  return t.length >= 6
}

function parseCoordinatorReport(report: string): Block[] {
  const lines = report
    .replace(/\r\n/g, '\n')
    .split('\n')
    .map((l) => l.replace(/\s+$/g, ''))

  const blocks: Block[] = []
  let i = 0

  let pendingUL: string[] | null = null
  let pendingOL: string[] | null = null

  const flushLists = () => {
    if (pendingUL && pendingUL.length) blocks.push({ type: 'ul', items: pendingUL })
    if (pendingOL && pendingOL.length) blocks.push({ type: 'ol', items: pendingOL })
    pendingUL = null
    pendingOL = null
  }

  const pushP = (text: string) => {
    flushLists()
    blocks.push({ type: 'p', text })
  }

  while (i < lines.length) {
    const cur = (lines[i] ?? '').trim()

    // blank -> small spacer
    if (!cur) {
      flushLists()
      blocks.push({ type: 'spacer' })
      i++
      continue
    }

    // If current line is a rule, skip it
    if (isRuleLine(cur)) {
      i++
      continue
    }

    // Title/Section detection:
    // In your report, headings are usually:
    //   TEXT
    //   =======   (underline)
    // or:
    //   TEXT
    //   -------   (underline)
    //
    // We render underline for BOTH rule types (as requested).
    if (isAllCapsTitle(cur)) {
      const next = (lines[i + 1] ?? '').trim()
      const underline = isEqualsRule(next) || isDashesRule(next)

      // First heading -> h1, rest -> h2
      flushLists()

      const hasPrevHeading = blocks.some((b) => b.type === 'h1' || b.type === 'h2')
      if (!hasPrevHeading) {
        blocks.push({ type: 'h1', text: cur, underline })
      } else {
        blocks.push({ type: 'h2', text: cur, underline })
      }

      // consume underline rule line if present
      if (underline) i += 2
      else i += 1

      continue
    }

    // bullet items
    if (cur.startsWith('• ')) {
      if (pendingOL) flushLists()
      if (!pendingUL) pendingUL = []
      pendingUL.push(cur.replace(/^•\s+/, ''))
      i++
      continue
    }

    // numbered list items like "1. ..."
    if (/^\d+\.\s+/.test(cur)) {
      if (pendingUL) flushLists()
      if (!pendingOL) pendingOL = []
      pendingOL.push(cur.replace(/^\d+\.\s+/, ''))
      i++
      continue
    }

    // normal paragraph line
    pushP(cur)
    i++
  }

  flushLists()
  return blocks
}

function LabelValueLine({ text }: { text: string }) {
  // Render "Estimated Range: $..." with bold label
  const idx = text.indexOf(':')
  if (idx === -1) return <span>{text}</span>

  const label = text.slice(0, idx + 1)
  const value = text.slice(idx + 1).trim()

  return (
    <span>
      <span className="font-semibold">{label}</span> {value}
    </span>
  )
}

export default function CoordinatorReportView({ report }: Props) {
  const blocks = React.useMemo(() => parseCoordinatorReport(report), [report])

  return (
    <div className="rounded-xl border border-border bg-background/30 p-6">
      {/* tighter overall spacing */}
      <div className="space-y-3">
        {blocks.map((b, idx) => {
          if (b.type === 'spacer') return <div key={idx} className="h-1" />

          if (b.type === 'h1') {
            return (
              <div key={idx}>
                <h1 className="text-2xl font-bold tracking-tight">{b.text}</h1>
                {b.underline && <div className="mt-2 h-px w-full bg-border" />}
              </div>
            )
          }

          if (b.type === 'h2') {
            return (
              <div key={idx}>
                <h2 className="text-lg font-semibold tracking-wide">{b.text}</h2>
                {b.underline && <div className="mt-1 h-px w-full bg-border/70" />}
              </div>
            )
          }

          if (b.type === 'p') {
            return (
              <p key={idx} className="text-sm leading-5 text-foreground/90">
                <LabelValueLine text={b.text} />
              </p>
            )
          }

          if (b.type === 'ul') {
            return (
              <ul
                key={idx}
                className="list-disc pl-5 space-y-1 text-sm leading-5 text-foreground/90"
              >
                {b.items.map((it, j) => (
                  <li key={j} className="whitespace-pre-wrap">
                    {it}
                  </li>
                ))}
              </ul>
            )
          }

          // ordered list
          return (
            <ol
              key={idx}
              className="list-decimal pl-5 space-y-1 text-sm leading-5 text-foreground/90"
            >
              {b.items.map((it, j) => (
                <li key={j} className="whitespace-pre-wrap">
                  {it}
                </li>
              ))}
            </ol>
          )
        })}
      </div>
    </div>
  )
}
