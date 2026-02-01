'use client'

import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

import '../../../global.css'
import CountdownTimer from '@/components/CountdownTimer'
import { Gem } from 'lucide-react'

import Footer from '@/components/Footer'
import ArtGrid, { type ArtUI } from '@/components/ArtGrid'

import fallbackImg from '@/assets/nft-ape.jpg' // ✅ fallback if no backend images

import BidButton from '@/components/BidButton'
import Lightbox from '@/components/LightBox'
import PreviewButton from '@/components/PreviewButton'

import Image from 'next/image'
import { extractUserId, type MeResponse } from '@/lib/auth'

type PictureDTO = {
  id: string
  item_id: string
  url: string
  created_at: string
}

type Item = {
  id: string
  seller_id: string
  seller_username: string
  title: string
  description?: string
  author?: string
  status?: string
  base_price?: number
  highest_bid_amount?: number
  highest_bidder_id?: string
  highest_bid_time?: Date
  increment?: number

  time_start?: string
  time_end?: string
  created_at?: string

  year_created?: number
  height?: number
  width?: number
  features?: any

  current_price?: number

  pictures: PictureDTO[] // ✅ from backend
}

type ListItemsResponse = {
  items: Array<{
    id: string
    title: string
    seller_username: string
    author: string
    base_price?: number
    highest_bid_amount?: number
    time_end?: string
    pictures?: PictureDTO[] // ✅ include for "More From This User" images
  }>
  next_cursor: string | null
}

type GetItemResponse = { item: Item }

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
  })

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data?.error?.message ?? `Request failed (${res.status})`)
  }

  return res.json()
}

function formatHighestBid(price?: number) {
  if (typeof price !== 'number') return 'SGD —'
  return `SGD ${price.toLocaleString()}`
}

function formatDue(iso?: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString()
}

function formatMaybeNumber(n?: number, suffix = '') {
  if (typeof n !== 'number') return '—'
  return `${n}${suffix}`
}

function stringifyFeatures(features: any) {
  if (!features) return null
  if (typeof features === 'string') return features.trim() || null
  try {
    return JSON.stringify(features, null, 2)
  } catch {
    return null
  }
}

function pickFirstImageUrl(pictures?: PictureDTO[] | null) {
  if (!pictures || pictures.length === 0) return fallbackImg.src
  const url = pictures[0]?.url?.trim()
  return url && url.length > 0 ? url : fallbackImg.src
}

function toLightboxImages(pictures?: PictureDTO[] | null) {
  if (!pictures || pictures.length === 0) {
    return [{ src: fallbackImg.src, alt: 'Artwork image' }]
  }
  const imgs = pictures
    .map((p, i) => ({
      src: (p.url || '').trim(),
      alt: `Image ${i + 1}`,
    }))
    .filter((x) => x.src.length > 0)

  return imgs.length ? imgs : [{ src: fallbackImg.src, alt: 'Artwork image' }]
}

export default function ItemPage() {
  const params = useParams()

  // If your folder is /items/[itemid], then params.itemid exists (could be string | string[])
  const itemIdRaw = (params as any)?.itemid
  const itemId =
    typeof itemIdRaw === 'string' ? itemIdRaw : (itemIdRaw?.[0] ?? '')

  const [refreshKey, setRefreshKey] = useState(0)

  const [isOpen, setIsOpen] = useState(false)
  const [startIndex, setStartIndex] = useState(0)

  const [item, setItem] = useState<Item | null>(null)
  const [loadingItem, setLoadingItem] = useState(true)
  const [errorItem, setErrorItem] = useState<string | null>(null)

  const [moreItems, setMoreItems] = useState<ArtUI[]>([])
  const [loadingMore, setLoadingMore] = useState(false)
  const [errorMore, setErrorMore] = useState<string | null>(null)

  // ✅ Auth state
  const [userId, setUserId] = useState<string | null>(null)
  const [authLoading, setAuthLoading] = useState(true)

  const [banner, setBanner] = useState<{
    type: 'success' | 'error'
    message: string
  } | null>(null)

  /* ───────────── Get current user ───────────── */
  useEffect(() => {
    let cancelled = false

    async function run() {
      try {
        const res = await fetch('/api/auth/me', {
          credentials: 'include',
          cache: 'no-store',
        })

        if (!res.ok) {
          if (!cancelled) setUserId(null)
          return
        }

        const data = (await res.json().catch(() => null)) as MeResponse
        const uid = extractUserId(data)

        if (!cancelled) setUserId(uid)
      } catch {
        if (!cancelled) setUserId(null)
      } finally {
        if (!cancelled) setAuthLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [])

  /* ───────────── Fetch item ───────────── */
  useEffect(() => {
    let cancelled = false

    async function run() {
      setLoadingItem(true)
      setErrorItem(null)
      try {
        const data = await fetchJson<GetItemResponse>(`/api/items/${itemId}`)
        if (!cancelled) setItem(data.item)
      } catch (e: any) {
        if (!cancelled) setErrorItem(e.message)
      } finally {
        if (!cancelled) setLoadingItem(false)
      }
    }

    if (itemId) run()
    return () => {
      cancelled = true
    }
  }, [itemId, refreshKey])

  /* ───────────── Fetch more from same seller ───────────── */
  useEffect(() => {
    let cancelled = false
    const seller_id = item?.seller_id

    async function run() {
      if (!seller_id) return
      setLoadingMore(true)
      setErrorMore(null)
      try {
        const url = `/api/items?seller_id=${encodeURIComponent(seller_id)}`
        const data = await fetchJson<ListItemsResponse>(url)

        if (!cancelled) {
          setMoreItems(
            data.items
              .filter((x) => x.id !== itemId)
              .map((x) => ({
                id: x.id,
                title: x.title,
                seller_username: x.seller_username,
                author: x.author,
                highestBid: formatHighestBid(
                  x.highest_bid_amount ?? x.base_price
                ),
                due: formatDue(x.time_end),
                img: pickFirstImageUrl(x.pictures),
              }))
          )
        }
      } catch (e: any) {
        if (!cancelled) setErrorMore(e.message)
      } finally {
        if (!cancelled) setLoadingMore(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [item?.seller_id, itemId])

  /* ───────────── Auction ended logic ───────────── */
  const auctionEnded = useMemo(() => {
    if (!item?.time_end) return false
    const end = new Date(item.time_end)
    return !Number.isNaN(end.getTime()) && end.getTime() <= Date.now()
  }, [item?.time_end])

  // ✅ Only allow bids if logged in, not seller, and not ended
  const canBid = useMemo(() => {
    if (authLoading) return false
    if (!userId) return false
    if (!item) return false
    if (auctionEnded) return false
    if (item.seller_id === userId) return false
    return true
  }, [authLoading, userId, item, auctionEnded])

  const featuresText = stringifyFeatures(item?.features)

  // ✅ Build images dynamically from backend pictures
  const itemImages = useMemo(
    () => toLightboxImages(item?.pictures),
    [item?.pictures]
  )

  // ✅ Hero image uses first backend image
  const heroSrc = itemImages[0]?.src ?? fallbackImg.src

  const currentPrice = useMemo(() => {
    const n = item?.highest_bid_amount ?? item?.base_price
    return typeof n === 'number' ? n : null
  }, [item?.highest_bid_amount, item?.base_price])

  return (
    <div className="min-h-screen bg-background pt-16">
      {banner && (
        <div className="fixed top-20 left-0 right-0 z-40 flex justify-center px-4">
          <div
            className={`relative flex items-center gap-4 rounded-lg px-4 pr-10 py-3 text-sm shadow
        ${
          banner.type === 'success'
            ? 'bg-green-100 text-green-700'
            : 'bg-red-100 text-red-700'
        }`}
          >
            <span className="whitespace-nowrap">{banner.message}</span>

            <button
              onClick={() => setBanner(null)}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-1 text-lg leading-none opacity-70 hover:opacity-100"
              aria-label="Close"
            >
              ×
            </button>
          </div>
        </div>
      )}
      {/* Hero */}
      <section>
        <div className="relative w-full aspect-[16/10] lg:aspect-[21/9] overflow-hidden">
          <button
            className="w-full h-full cursor-zoom-in"
            onClick={() => {
              setStartIndex(0)
              setIsOpen(true)
            }}
          >
            <Image
              src={heroSrc}
              alt={item?.title ?? 'Artwork'}
              fill
              className="object-cover"
            />
          </button>
        </div>
      </section>

      <Lightbox
        images={itemImages}
        initialIndex={startIndex}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />

      {/* Content */}
      <section className="container mx-auto px-4 lg:px-6 -mt-16 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left */}
          <div className="lg:col-span-2 space-y-6">
            {errorItem && (
              <div className="rounded-lg border border-destructive/40 bg-card p-4 text-sm">
                <div className="font-semibold">Failed to load item</div>
                <div className="text-muted-foreground">{errorItem}</div>
              </div>
            )}

            <h1 className="text-4xl font-bold">
              {item?.title ?? (loadingItem ? 'Loading...' : '—')}
            </h1>

            {/* ✅ Current/Highest bid display */}
            <div className="rounded-xl border bg-card p-4 mt-10">
              <p className="text-muted-foreground text-sm">
                {item?.highest_bid_amount ? 'Current Bid' : 'Base Price'}
              </p>
              <p className="font-mono text-2xl font-semibold">
                {currentPrice !== null
                  ? `SGD ${currentPrice.toLocaleString()}`
                  : '—'}
              </p>
            </div>

            <div className="lg:hidden space-y-3">
              <CountdownTimer targetDate={item?.time_end} />

              {/* ✅ Bid button gating */}
              {canBid && (
                <BidButton
                  item={{
                    id: item?.id,
                    title: item?.title,
                    base_price: item?.base_price,
                    increment: item?.increment ?? 1,
                    highest_bid_amount: item?.highest_bid_amount,
                  }}
                  setRefreshKey={() => setRefreshKey((k) => k + 1)}
                  onSuccess={() =>
                    setBanner({
                      type: 'success',
                      message: 'Bid placed successfully',
                    })
                  }
                />
              )}

              {/* ✅ Helpful hints */}
              {!authLoading && !userId && (
                <p className="text-sm text-muted-foreground text-center">
                  Please login to place a bid.
                </p>
              )}
              {!authLoading && userId && userId === item?.seller_id && (
                <p className="text-sm text-muted-foreground text-center">
                  You cannot bid on your own item.
                </p>
              )}
              {!authLoading && userId && auctionEnded && (
                <p className="text-sm text-muted-foreground text-center">
                  Auction ended.
                </p>
              )}
            </div>

            <div>
              <p className="text-muted-foreground text-sm">Seller</p>
              <div className="flex items-center gap-2">
                <Gem className="w-5 h-5 text-primary" />
                <span>{item?.seller_username ?? '—'}</span>
              </div>
            </div>

            <div>
              <p className="text-muted-foreground text-sm mb-2">Description</p>
              <p>{item?.description ?? '—'}</p>
            </div>

            {/* Details */}
            <div className="border rounded-xl p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-muted-foreground">Width</p>
                <p>{formatMaybeNumber(item?.width, ' cm')}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Height</p>
                <p>{formatMaybeNumber(item?.height, ' cm')}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Year Created</p>
                <p>{item?.year_created ?? '—'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Status</p>
                <p>{item?.status ?? '—'}</p>
              </div>
            </div>

            {featuresText && (
              <pre className="border rounded-lg p-3 text-xs whitespace-pre-wrap">
                {featuresText}
              </pre>
            )}

            <PreviewButton itemName={item?.title} />
          </div>

          {/* Right */}
          <div className="hidden lg:flex flex-col gap-4">
            <CountdownTimer targetDate={item?.time_end} />

            {/* ✅ Bid button gating */}
            {canBid && (
              <BidButton
                item={{
                  id: item?.id,
                  title: item?.title,
                  base_price: item?.base_price,
                  increment: item?.increment ?? 1,
                  highest_bid_amount: item?.highest_bid_amount,
                }}
                setRefreshKey={() => setRefreshKey((k) => k + 1)}
              />
            )}

            {/* ✅ Helpful hints */}
            {!authLoading && !userId && (
              <p className="text-sm text-muted-foreground text-center">
                Please login to place a bid.
              </p>
            )}
            {!authLoading && userId && userId === item?.seller_id && (
              <p className="text-sm text-muted-foreground text-center">
                You cannot bid on your own item.
              </p>
            )}
            {!authLoading && userId && auctionEnded && (
              <p className="text-sm text-muted-foreground text-center">
                Auction ended.
              </p>
            )}
          </div>
        </div>
      </section>

      {/* More from user */}
      <section className="container mx-auto px-4 lg:px-6 mt-24">
        <div className="mb-8 flex items-center justify-between gap-4">
          <h2 className="text-3xl font-bold">More From This User</h2>

          {/* ✅ Button -> user profile */}
          {item?.seller_id && (
            <Link
              href={`/users/${item.seller_id}`}
              className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition"
            >
              View Profile
            </Link>
          )}
        </div>

        <ArtGrid items={moreItems} loading={loadingMore} error={errorMore} />
      </section>

      <Footer />
    </div>
  )
}
