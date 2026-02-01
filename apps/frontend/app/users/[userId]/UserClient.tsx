'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

import ArtGrid, { type ArtUI } from '@/components/ArtGrid'
import Pagination from '@/components/Pagination'

import UserHeader from './components/UserHeader'
import UserStats from './components/UserStats'

type PictureDTO = {
  id: string
  item_id: string
  url: string
  created_at: string
}

type ItemDTO = {
  id: string
  title: string
  seller_id?: string
  seller_username: string | null
  author: string | null
  time_end: string
  base_price: number | string
  highest_bid_amount: number | string | undefined
  pictures: PictureDTO[] // ✅ ADD THIS
}

type ListItemsResponse =
  | { items: ItemDTO[]; next_cursor?: string | null }
  | { data: ItemDTO[]; next_cursor?: string | null }
  | ItemDTO[]

const LIMIT = 12

function normalize(res: ListItemsResponse): {
  items: ItemDTO[]
  next_cursor: string | null
} {
  if (Array.isArray(res)) return { items: res, next_cursor: null }
  if ('items' in res)
    return { items: res.items, next_cursor: res.next_cursor ?? null }
  if ('data' in res)
    return { items: res.data, next_cursor: res.next_cursor ?? null }
  return { items: [], next_cursor: null }
}

function formatDue(iso: string) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yyyy = d.getFullYear()
  return `${dd}-${mm}-${yyyy}`
}

function formatBid(n: number | string | undefined) {
  if (n == undefined) return undefined
  const num = typeof n === 'string' ? Number(n) : n
  if (!Number.isFinite(num)) return String(n)
  return `${num.toLocaleString()} SGD`
}

export default function UserClient() {
  const params = useParams<{ userId: string }>()
  const userId = params?.userId

  // cursor pagination state
  const [page, setPage] = useState(1)
  const [nextCursor, setNextCursor] = useState<string | null>(null)

  // data
  const [items, setItems] = useState<ArtUI[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const buildUrl = (cursor: string | null) => {
    const qs = new URLSearchParams()
    qs.set('limit', String(LIMIT))

    // your backend param name can be userId / seller_id / sellerId, etc.
    // choose ONE and keep it consistent with your Next.js route handler.
    qs.set('seller_id', userId)

    if (cursor) qs.set('cursor', cursor)
    return `/api/items?${qs.toString()}`
  }
  console.log(items)

  async function fetchPage(opts: {
    mode: 'reset' | 'append'
    cursor: string | null
  }) {
    const isReset = opts.mode === 'reset'

    try {
      isReset ? setLoading(true) : setLoadingMore(true)
      setError(null)

      const r = await fetch(buildUrl(opts.cursor), {
        method: 'GET',
        cache: 'no-store',
      })

      if (!r.ok) {
        const text = await r.text()
        let msg = `Request failed (${r.status})`
        try {
          const data = text ? JSON.parse(text) : {}
          msg = data?.error?.message ?? data?.message ?? msg
        } catch {}
        throw new Error(msg)
      }

      const json = (await r.json()) as ListItemsResponse
      const { items: raw, next_cursor } = normalize(json)

      const mapped: ArtUI[] = raw.map((it) => ({
        id: it.id,
        title: it.title,
        seller_username: it.seller_username?.trim() || 'Unknown',
        author: it.author?.trim() || 'Unknown',
        basePrice: formatBid(it.base_price),
        highestBid: formatBid(it.highest_bid_amount),
        due: formatDue(it.time_end),
        img: it.pictures[0].url,
      }))

      if (isReset) setItems(mapped)
      else setItems((prev) => [...prev, ...mapped])

      setNextCursor(next_cursor)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      if (isReset) setItems([])
      setNextCursor(null)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  // initial load / when userId changes
  useEffect(() => {
    if (!userId) return
    setPage(1)
    setNextCursor(null)
    fetchPage({ mode: 'reset', cursor: null })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  // when clicking "See More"
  useEffect(() => {
    if (!userId) return
    if (page === 1) return
    if (!nextCursor) return
    fetchPage({ mode: 'append', cursor: nextCursor })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  const hasNext = !!nextCursor && !loading && !loadingMore

  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="container mx-auto px-6">
        <UserHeader userId={userId} />
        {
          // Remove The Comment After Implemented
          // <UserStats /> 
        }
        <ArtGrid items={items} loading={loading} error={error} />

        <div className="mt-8 flex justify-center">
          <Pagination page={page} hasNext={hasNext} onPageChange={setPage} />
        </div>

        {loadingMore && (
          <div className="mt-3 text-center text-sm text-muted-foreground">
            Loading more...
          </div>
        )}
      </div>
    </div>
  )
}
