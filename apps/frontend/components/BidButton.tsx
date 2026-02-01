'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { Button } from './ui/Button'

type ItemForBid = {
  id: string | undefined
  base_price: number | undefined
  increment: number | undefined
  title: string | undefined
  highest_bid_amount: number | undefined
}

type BidButtonProps = {
  item: ItemForBid
  triggerText?: string
  setRefreshKey: () => void
  onSuccess?: () => void
}

function fmtSGD(n: number) {
  return n.toLocaleString()
}

export default function BidButton({
  item,
  triggerText = 'Place Bid',
  setRefreshKey,
  onSuccess,
}: BidButtonProps) {
  const [bid, setBid] = React.useState('')
  const [submitting, setSubmitting] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  // ✅ Control dialog
  const [open, setOpen] = React.useState(false)

  const currentPrice = item.base_price ?? 0
  const highestBid = item.highest_bid_amount
  const increment = item.increment ?? 0
  const minBid = highestBid
    ? highestBid + increment
    : currentPrice == 0
      ? 1
      : currentPrice

  const bidInt = bid === '' ? NaN : parseInt(bid, 10)

  const canSubmit = Number.isFinite(bidInt) && bidInt >= minBid && !submitting

  async function submitBid() {
    if (!canSubmit) return

    if (!item.id) {
      setError('Missing item id.')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const res = await fetch(`/api/items/${item.id}/bids`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ price: bidInt }),
      })

      if (!res.ok) {
        const text = await res.text()
        const data = text ? JSON.parse(text) : {}

        throw new Error(
          data?.error?.message ??
            data?.message ??
            (res.status === 401
              ? 'Please log in to place a bid.'
              : 'Failed to place bid')
        )
      }

      // ✅ Reset state
      setBid('')
      setError(null)

      // ✅ Close dialog
      setOpen(false)
      setRefreshKey()
      onSuccess?.()
    } catch (e: any) {
      setError(e?.message ?? 'Failed to place bid')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      {/* Trigger */}
      <Dialog.Trigger asChild>
        <Button className="h-12 w-full bg-purple-600 text-white hover:bg-purple-700">
          {triggerText}
        </Button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm" />

        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-neutral-800 p-6 shadow-lg">
          <Dialog.Title className="mb-2 text-xl font-bold">
            Place a Bid
          </Dialog.Title>

          <Dialog.Description className="mb-6 text-sm text-muted-foreground">
            You are bidding on{' '}
            <span className="font-medium text-primary">{item.title}</span>
          </Dialog.Description>

          <div className="space-y-4">
            {/* Price Info */}
            <div className="flex justify-between rounded-lg bg-secondary/40 p-4">
              <div>
                <p className="text-xs text-muted-foreground">
                  {highestBid && highestBid > 0 ? 'Highest Bid' : 'Base Price'}
                </p>

                <p className="font-semibold">
                  SGD {fmtSGD(highestBid ?? currentPrice)}
                </p>
              </div>

              <div className="text-right">
                <p className="text-xs text-muted-foreground">Minimum Bid</p>

                <p className="font-semibold text-primary">
                  SGD {fmtSGD(minBid)}
                </p>
              </div>
            </div>

            {/* Input */}
            <div>
              <label className="mb-1 block text-sm font-medium">Your Bid</label>

              <div className="relative">
                <input
                  type="text"
                  inputMode="numeric"
                  value={bid}
                  onChange={(e) => setBid(e.target.value.replace(/[^\d]/g, ''))}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 pr-14"
                  placeholder="Enter amount"
                />

                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                  SGD
                </span>
              </div>
            </div>

            {/* Error */}
            {error && <p className="text-sm text-red-400">{error}</p>}

            {/* Buttons */}
            <Button fullWidth onClick={() => setBid(String(minBid))}>
              Set Minimum Bid
            </Button>

            <Button fullWidth disabled={!canSubmit} onClick={submitBid}>
              {submitting ? 'Submitting…' : 'Submit Bid'}
            </Button>
          </div>

          {/* Close Button */}
          <Dialog.Close asChild>
            <button className="absolute right-4 top-4 text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}