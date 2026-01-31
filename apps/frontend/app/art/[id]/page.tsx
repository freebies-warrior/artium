'use client'

import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'next/navigation'

import '../../../global.css'
import Navbar from '@/components/NavBar'
import CountdownTimer from '@/components/CountdownTimer'
import { Gem } from 'lucide-react'

import Footer from '@/components/Footer'
import ArtGrid, { type ArtUI } from '@/components/ArtGrid'

import heroNft from '@/assets/nft-hero-1.jpg'
import heroNft2 from '@/assets/nft-ape.jpg'

import BidButton from '@/components/BidButton'
import Lightbox from '@/components/LightBox'
import PreviewButton from '@/components/PreviewButton'

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

  // optional if your backend has it
  current_price?: number
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

export default function ArtPage() {
  const params = useParams()
  const itemId = useMemo(() => {
    const raw = (params as any)?.item_id ?? (params as any)?.id
    return typeof raw === 'string' ? raw : ''
  }, [params])
  const [refreshKey, setRefreshKey] = useState(0)


  const [isOpen, setIsOpen] = useState(false)
  const [startIndex, setStartIndex] = useState(0)

  const itemImages = [
    { src: heroNft.src, alt: 'Image 1' },
    { src: heroNft2.src, alt: 'Image 2' },
  ]

  const [item, setItem] = useState<Item | null>(null)
  const [loadingItem, setLoadingItem] = useState(true)
  const [errorItem, setErrorItem] = useState<string | null>(null)

  const [moreItems, setMoreItems] = useState<ArtUI[]>([])
  const [loadingMore, setLoadingMore] = useState(false)
  const [errorMore, setErrorMore] = useState<string | null>(null)

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

  /* ───────────── Fetch more from same author ───────────── */
  useEffect(() => {
    let cancelled = false
    const seller_id = item?.seller_id;

    async function run() {
      setLoadingMore(true)
      setErrorMore(null)
      try {
        const url = `/api/items?seller_id=${encodeURIComponent(seller_id ?? '')}`
        const data = await fetchJson<ListItemsResponse>(url)

        if (!cancelled) {
          setMoreItems(
            data.items
              .filter((x) => x.id !== itemId)
              .map((x) => {
                return {
                  id: x.id,
                  title: x.title,
                  seller_username: x.seller_username,
                  author: x.author, 
                  highestBid: formatHighestBid(x.highest_bid_amount ?? x.base_price),
                  due: formatDue(x.time_end),
                }
              })
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
  }, [item?.seller_username, itemId])

  /* ───────────── Auction ended logic ───────────── */
  const auctionEnded = useMemo(() => {
    if (!item?.time_end) return false
    const end = new Date(item.time_end)
    return !Number.isNaN(end.getTime()) && end.getTime() <= Date.now()
  }, [item?.time_end])

  const featuresText = stringifyFeatures(item?.features)
  console.log("HAHA: " + item?.highest_bid_amount);
  return (
    <div className="min-h-screen bg-background pt-16">
      <Navbar />

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
            <img
              src={itemImages[0].src}
              className="w-full h-full object-cover"
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
            <h1 className="text-4xl font-bold">{item?.title}</h1>

            <div className="lg:hidden">
              <CountdownTimer targetDate={item?.time_end} />
              {!auctionEnded && (
                <BidButton
                  item={{
                    id: item?.id,
                    title: item?.title,
                    base_price:  item?.base_price,
                    increment: item?.increment ?? 1,
                    highest_bid_amount: item?.highest_bid_amount,
                  }}
                  setRefreshKey= {() => setRefreshKey(refreshKey + 1)}
                />
              )}
            </div>

            <div>
              <p className="text-muted-foreground text-sm">Seller</p>
              <div className="flex items-center gap-2">
                <Gem className="w-5 h-5 text-primary" />
                <span>{item?.seller_username}</span>
              </div>
            </div>

            <div>
              <p className="text-muted-foreground text-sm mb-2">Description</p>
              <p>{item?.description}</p>
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
                <p>{item?.status}</p>
              </div>
            </div>

            {featuresText && (
              <pre className="border rounded-lg p-3 text-xs whitespace-pre-wrap">
                {featuresText}
              </pre>
            )}

            <PreviewButton />
          </div>

          {/* Right */}
          <div className="hidden lg:flex flex-col gap-4">
            <CountdownTimer targetDate={item?.time_end} />
            {!auctionEnded && (
              <BidButton
                item={{
                    id: item?.id,
                    title: item?.title,
                    base_price:  item?.base_price,
                    increment: item?.increment ?? 1,
                    highest_bid_amount: item?.highest_bid_amount,
                }}
                setRefreshKey= {() => setRefreshKey(refreshKey + 1)}
              />
            )}
          </div>
        </div>
      </section>

      {/* More from user */}
      <section className="container mx-auto px-4 lg:px-6 mt-24">
        <h2 className="text-3xl font-bold mb-8">More From This User</h2>
        <ArtGrid items={moreItems} loading={loadingMore} error={errorMore} />
      </section>

      <Footer />
    </div>
  )
}
