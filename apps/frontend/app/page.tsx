'use client';

import '../global.css';
import { useEffect, useState } from 'react';

import Footer from '@/components/Footer';
import HeroSection from '@/components/HeroSections';
import Tabs from '@/components/Tabs';
import ArtGrid, { type ArtUI } from '@/components/ArtGrid';
import SellerGrid from '@/components/SellerGrid';
import Pagination from '@/components/Pagination';

type ItemDTO = {
  id: string;
  title: string;
  author: string | null;
  time_end: string;
  base_price: number | string;
};

type ListItemsResponse =
  | { items: ItemDTO[]; next_cursor?: string | null }
  | { data: ItemDTO[]; next_cursor?: string | null }
  | ItemDTO[];

const LIMIT = 4;

function normalize(res: ListItemsResponse): { items: ItemDTO[]; next_cursor: string | null } {
  if (Array.isArray(res)) return { items: res, next_cursor: null };
  if ('items' in res) return { items: res.items, next_cursor: res.next_cursor ?? null };
  if ('data' in res) return { items: res.data, next_cursor: res.next_cursor ?? null };
  return { items: [], next_cursor: null };
}

function formatDue(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const dd = String(d.getDate()).padStart(2, '0');
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const yyyy = d.getFullYear();
  return `${dd}-${mm}-${yyyy}`;
}

function formatBid(n: number | string) {
  const num = typeof n === 'string' ? Number(n) : n;
  if (!Number.isFinite(num)) return String(n);
  return `${num.toLocaleString()} SGD`;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<'arts' | 'sellers'>('arts');

  // search typing + submitted query
  const [search, setSearch] = useState('');
  const [appliedQuery, setAppliedQuery] = useState('');

  // cursor pagination state
  const [page, setPage] = useState(1);
  const [nextCursor, setNextCursor] = useState<string | null>(null);

  // data
  const [items, setItems] = useState<ArtUI[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleTabChange(tab: 'arts' | 'sellers') {
    setActiveTab(tab);
    setPage(1);
  }

  const onSearchSubmit = () => {
    setAppliedQuery(search.trim());
    setPage(1);
  };

  // ✅ use Next.js proxy route
  const buildUrl = (cursor: string | null) => {
    const qs = new URLSearchParams();
    qs.set('limit', String(LIMIT));
    if (appliedQuery) qs.set('q', appliedQuery);

    // IMPORTANT:
    // Keep this param name aligned with your backend.
    // If backend expects "cursor", keep as-is.
    // If backend expects "next_cursor", change to qs.set('next_cursor', cursor)
    if (cursor) qs.set('cursor', cursor);

    return `/api/items?${qs.toString()}`;
  };

  async function fetchPage(opts: { mode: 'reset' | 'append'; cursor: string | null }) {
    const isReset = opts.mode === 'reset';

    try {
      isReset ? setLoading(true) : setLoadingMore(true);
      setError(null);

      const r = await fetch(buildUrl(opts.cursor), { method: 'GET', cache: 'no-store' });
      if (!r.ok) {
        const text = await r.text();
        let msg = `Request failed (${r.status})`;
        try {
          const data = text ? JSON.parse(text) : {};
          msg = data?.error?.message ?? data?.message ?? msg;
        } catch {}
        throw new Error(msg);
      }

      const json = (await r.json()) as ListItemsResponse;
      const { items: raw, next_cursor } = normalize(json);

      const mapped: ArtUI[] = raw.map((it) => ({
        id: it.id,
        title: it.title,
        author: it.author?.trim() || 'Unknown',
        highestBid: formatBid(it.base_price),
        due: formatDue(it.time_end),
      }));

      if (isReset) setItems(mapped);
      else setItems((prev) => [...prev, ...mapped]);

      setNextCursor(next_cursor);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
      if (isReset) setItems([]);
      setNextCursor(null);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }

  // Initial load + when user submits a new search query
  useEffect(() => {
    if (activeTab !== 'arts') return;
    fetchPage({ mode: 'reset', cursor: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, appliedQuery]);

  // When user clicks "See More" (page increments)
  useEffect(() => {
    if (activeTab !== 'arts') return;
    if (page === 1) return;
    if (!nextCursor) return;

    fetchPage({ mode: 'append', cursor: nextCursor });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const hasNext = !!nextCursor && !loading && !loadingMore;

  return (
    <div className="min-h-screen bg-background">
      <main className="pt-16">
        <HeroSection
          search={search}
          onSearchChange={setSearch}
          onSearchSubmit={onSearchSubmit}
        />

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
          <SellerGrid />
        )}
      </main>

      <Footer />
    </div>
  );
}
