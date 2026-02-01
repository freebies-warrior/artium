'use client'

import '../global.css'
import { motion } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'

export type ArtUI = {
  id: string
  title: string
  seller_username: string
  author: string
  basePrice?: string
  highestBid?: string
  due: string
  img: string
}

const ArtCard = ({ item, index }: { item: ArtUI; index: number }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.05 }}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.98 }}
      className="art-card cursor-pointer"
    >
      <Link href={`/items/${item.id}`} className="block">
        <div className="relative aspect-square overflow-hidden">
          <Image
            src={item.img}
            alt={item.title}
            fill
            className="object-cover transition-transform duration-500 hover:scale-110"
          />
        </div>

        <div className="p-4">
          <h3 className="mb-2 font-semibold text-foreground">{item.title}</h3>

          <div className="mb-4 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-900 text-sm font-semibold text-foreground">
              {item.seller_username.charAt(0).toUpperCase()}
            </div>
            <span className="text-sm text-muted-foreground">
              {item.seller_username}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">
                {item.highestBid && item.highestBid != 'SGD 0'
                  ? 'Highest Bid'
                  : 'Base Price'}
              </p>
              <p className="font-mono text-sm font-medium">
                {item.highestBid ?? item.basePrice}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Due</p>
              <p className="font-mono text-sm font-medium">{item.due}</p>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

type ArtGridProps = {
  items: ArtUI[]
  loading?: boolean
  error?: string | null
}

export default function ArtGrid({ items, loading, error }: ArtGridProps) {
  return (
    <section className="py-8">
      <div className="container mx-auto px-4">
        {error && (
          <div className="mb-6 rounded-lg border border-destructive/40 bg-card p-4 text-sm text-foreground">
            <div className="font-semibold">Failed to load items</div>
            <div className="text-muted-foreground">{error}</div>
          </div>
        )}

        {loading ? (
          <div className="text-sm text-muted-foreground">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {items.map((item, index) => (
              <ArtCard key={item.id} item={item} index={index} />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
