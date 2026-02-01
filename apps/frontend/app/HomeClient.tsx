'use client'

import '../global.css'
import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

import Footer from '@/components/Footer'
import HeroSection from '@/components/HeroSections'
import Tabs from '@/components/Tabs'
import ArtGrid, { type ArtUI } from '@/components/ArtGrid'
import SellerGrid, { type SellerUI } from '@/components/SellerGrid'
import Pagination from '@/components/Pagination'

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
  pictures: PictureDTO[]
}

type ListItemsResponse =
  | { items: ItemDTO[]; next_cursor?: string | null }
  | { data: ItemDTO[]; next_cursor?: string | null }
  | ItemDTO[]

// ✅ users api DTO (adjust fields to match your backend)
type UserDTO = {
  id: string
  username: string | null
  // ideally backend gives these; otherwise set to 0 and show only username
  items_count?: number | null
  volume?: number | string | null
}

type ListUsersResponse =
  | { users: UserDTO[]; next_cursor?: string | null }
  | { data: UserDTO[]; next_cursor?: string | null }
  | UserDTO[]

const LIMIT = 4
const SELLER_LIMIT = 24 // ✅ pick a reasonable number for SellerGrid

function normalizeItems(res: ListItemsResponse): {
  items: ItemDTO[]
  next_cursor: string | null
} {
  if (Array.isArray(res)) return { items: res, next_cursor: null }
  if ('items' in res) return { items: res.items, next_cursor: res.next_cursor ?? null }
  if ('data' in res) return { items: res.data, next_cursor: res.next_cursor ?? null }
  return { items: [], next_cursor: null }
}

function normalizeUsers(res: ListUsersResponse): {
  users: UserDTO[]
  next_cursor: string | null
} {
  if (Array.isArray(res)) return { users: res, next_cursor: null }
  if ('users' in res) return { users: res.users, next_cursor: res.next_cursor ?? null }
  if ('data' in res) return { users: res.data, next_cursor: res.next_cursor ?? null }
  return { users: [], next_cursor: null }
}

function formatDue(iso: string) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yyyy = d.getFullYear()
  return `${dd}-${mm}-${yyyy}`
}

function toNumber(n: number | string | undefined | null): number | null {
  if (n == null) return null
  const num = typeof n === 'string' ? Number(n) : n
  return Number.isFinite(num) ? num : null
}

function formatMoneySGD(n: number) {
  return `${n.toLocaleString()} SGD`
}

export default function HomeClient() {
  const [activeTab, setActiveTab] = useState<'arts' | 'sellers'>('arts')

  const params = useSearchParams()
  const router = useRouter()
  const verifyStatus = params.get('verify')
  const [dismissed, setDismissed] = useState(false)

  let banner: { message: string; type: 'success' | 'error' } | null = null
  if (!dismissed) {
    if (verifyStatus === 'failed') {
      banner = {
        message: 'This verification link is invalid or has expired.',
        type: 'error',
      }
    } else if (verifyStatus === 'success') {
      banner = {
        message: 'Your email has been verified successfully. You may now log in.',
        type: 'success',
      }
    }
  }

  // search typing + submitted query
  const [search, setSearch] = useState('')
  const [appliedQuery, setAppliedQuery] = useState('')

  // ARTS cursor pagination state
  const [page, setPage] = useState(1)
  const [nextCursor, setNextCursor] = useState<string | null>(null)

  // SELLERS cursor pagination state (optional)
  const [sellerPage, setSellerPage] = useState(1)
  const [nextSellerCursor, setNextSellerCursor] = useState<string | null>(null)

  // data (ARTS)
  const [items, setItems] = useState<ArtUI[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // data (SELLERS)
  const [sellers, setSellers] = useState<SellerUI[]>([])
  const [loadingSellers, setLoadingSellers] = useState(false)
  const [loadingMoreSellers, setLoadingMoreSellers] = useState(false)
  const [errorSellers, setErrorSellers] = useState<string | null>(null)

  function handleTabChange(tab: 'arts' | 'sellers') {
    setActiveTab(tab)
    setPage(1)
    setSellerPage(1)
  }

  const onSearchSubmit = () => {
    setAppliedQuery(search.trim())
    setPage(1)
    setSellerPage(1)
  }

  // ✅ items endpoint
  const buildItemsUrl = (cursor: string | null, limit: number) => {
    const qs = new URLSearchParams()
    qs.set('limit', String(limit))
    if (appliedQuery) qs.set('q', appliedQuery)
    if (cursor) qs.set('cursor', cursor)
    return `/api/items?${qs.toString()}`
  }

  // ✅ users endpoint
  const buildUsersUrl = (cursor: string | null, limit: number) => {
    const qs = new URLSearchParams()
    qs.set('limit', String(limit))
    if (appliedQuery) qs.set('q', appliedQuery)
    if (cursor) qs.set('cursor', cursor)
    return `/api/users?${qs.toString()}`
  }

  async function fetchArtsPage(opts: { mode: 'reset' | 'append'; cursor: string | null }) {
    const isReset = opts.mode === 'reset'
    try {
      isReset ? setLoading(true) : setLoadingMore(true)
      setError(null)

      const r = await fetch(buildItemsUrl(opts.cursor, LIMIT), {
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
      const { items: raw, next_cursor } = normalizeItems(json)

      const mapped: ArtUI[] = raw.map((it) => ({
        id: it.id,
        title: it.title,
        seller_username: it.seller_username?.trim() || 'Unknown',
        author: it.author?.trim() || 'Unknown',
        basePrice: formatMoneySGD(toNumber(it.base_price) ?? 0),
        highestBid:
          toNumber(it.highest_bid_amount) != null
            ? formatMoneySGD(toNumber(it.highest_bid_amount) ?? 0)
            : undefined,
        due: formatDue(it.time_end),
        img: it.pictures?.[0]?.url ?? '',
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

  // ✅ now sellers is same “shape” as fetchArtsPage, but hits /api/users
  async function fetchSellersPage(opts: { mode: 'reset' | 'append'; cursor: string | null }) {
    const isReset = opts.mode === 'reset'
    try {
      isReset ? setLoadingSellers(true) : setLoadingMoreSellers(true)
      setErrorSellers(null)

      const r = await fetch(buildUsersUrl(opts.cursor, SELLER_LIMIT), {
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

      const json = (await r.json()) as ListUsersResponse
      const { users: raw, next_cursor } = normalizeUsers(json)

      const mapped: SellerUI[] = raw.map((u) => {
        const usernameRaw = u.username?.trim() || 'Unknown'
        const clean = usernameRaw.replace(/^@+/, '')
        const name = clean.length ? clean : 'Unknown'
        const avatarLetter = name.charAt(0).toUpperCase() || 'U'

        const itemsCount = toNumber(u.items_count) ?? 0
        const volumeNum = toNumber(u.volume) ?? 0

        return {
          id: u.id,
          name,
          username: usernameRaw.startsWith('@') ? usernameRaw : `@${usernameRaw}`,
          avatarLetter,
          items: itemsCount,
          volume: formatMoneySGD(volumeNum),
        }
      })

      if (isReset) setSellers(mapped)
      else setSellers((prev) => [...prev, ...mapped])

      setNextSellerCursor(next_cursor)
    } catch (e) {
      setErrorSellers(e instanceof Error ? e.message : 'Unknown error')
      if (isReset) setSellers([])
      setNextSellerCursor(null)
    } finally {
      setLoadingSellers(false)
      setLoadingMoreSellers(false)
    }
  }

  // ARTS: initial load + when search changes
  useEffect(() => {
    if (activeTab !== 'arts') return
    setPage(1)
    fetchArtsPage({ mode: 'reset', cursor: null })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, appliedQuery])

  // SELLERS: initial load + when search changes
  useEffect(() => {
    if (activeTab !== 'sellers') return
    setSellerPage(1)
    fetchSellersPage({ mode: 'reset', cursor: null })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, appliedQuery])

  // ARTS: see more
  useEffect(() => {
    if (activeTab !== 'arts') return
    if (page === 1) return
    if (!nextCursor) return
    fetchArtsPage({ mode: 'append', cursor: nextCursor })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  // SELLERS: see more (only if you add seller pagination UI)
  useEffect(() => {
    if (activeTab !== 'sellers') return
    if (sellerPage === 1) return
    if (!nextSellerCursor) return
    fetchSellersPage({ mode: 'append', cursor: nextSellerCursor })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sellerPage])

  const hasNext = !!nextCursor && !loading && !loadingMore
  const hasNextSellers = !!nextSellerCursor && !loadingSellers && !loadingMoreSellers

  return (
    <div className="min-h-screen bg-background">
      <main className="pt-16">
        {banner && (
          <div className="fixed top-20 left-0 right-0 z-40 flex justify-center px-4">
            <div
              className={`relative w-full max-w-4xl rounded-lg px-4 py-3 text-center shadow
              ${
                banner.type === 'success'
                  ? 'bg-green-100 border border-green-300 text-green-700'
                  : 'bg-red-100 border border-red-300 text-red-700'
              }`}
            >
              <span>{banner.message}</span>

              <button
                onClick={() => {
                  setDismissed(true)
                  router.replace('/', { scroll: false })
                }}
                className="absolute right-4 top-1/2 -translate-y-1/2 font-bold"
                aria-label="Close banner"
              >
                ×
              </button>
            </div>
          </div>
        )}

        <HeroSection search={search} onSearchChange={setSearch} onSearchSubmit={onSearchSubmit} />
        <Tabs activeTab={activeTab} onTabChange={handleTabChange} />

        {activeTab === 'arts' ? (
          <>
            <ArtGrid items={items} loading={loading} error={error} />
            <div className="container mx-auto px-4 pb-8">
              <Pagination page={page} hasNext={hasNext} onPageChange={setPage} />
              {loadingMore && (
                <div className="mt-3 text-center text-sm text-muted-foreground">
                  Loading more...
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            <SellerGrid sellers={sellers} loading={loadingSellers} error={errorSellers} />

            <div className="container mx-auto px-4 pb-8">
              <Pagination page={sellerPage} hasNext={hasNextSellers} onPageChange={setSellerPage} />
              {loadingMoreSellers && (
                <div className="mt-3 text-center text-sm text-muted-foreground">
                  Loading more...
                </div>
              )}
            </div> 
          </>
        )}
      </main>

      <Footer />
    </div>
  )
}
