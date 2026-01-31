'use client'

import Link from 'next/link'
import '../global.css'
import { motion } from 'framer-motion'

export type SellerUI = {
  id: string
  name: string
  username: string
  avatarLetter: string
  items: number
  volume: string // e.g. "12,400 SGD"
}

function SellerCard({ seller, index }: { seller: SellerUI; index: number }) {
  return (
    <Link href={`/users/${seller.id}`} className="block">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: index * 0.05 }}
        whileHover={{ y: -4 }}
        whileTap={{ scale: 0.98 }}
        className="art-card"
      >
        <div className="p-5 cursor-pointer">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-900 text-base font-semibold text-foreground">
                {seller.avatarLetter}
              </div>

              <div>
                <p className="font-semibold text-foreground">{seller.name}</p>
                <p className="text-sm text-muted-foreground">{seller.username}</p>
              </div>
            </div>

            <button className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground hover:bg-secondary transition cursor-pointer">
              Visit
            </button>
          </div>
        </div>
      </motion.div>
    </Link>
  )
}

type SellerGridProps = {
  sellers: SellerUI[]
  loading?: boolean
  error?: string | null
}

export default function SellerGrid({ sellers, loading, error }: SellerGridProps) {
  return (
    <section className="py-8">
      <div className="container mx-auto px-4">
        {error && (
          <div className="mb-6 rounded-lg border border-destructive/40 bg-card p-4 text-sm text-foreground">
            <div className="font-semibold">Failed to load sellers</div>
            <div className="text-muted-foreground">{error}</div>
          </div>
        )}

        {loading ? (
          <div className="text-sm text-muted-foreground">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {sellers.map((seller, index) => (
              <SellerCard key={seller.id} seller={seller} index={index} />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
