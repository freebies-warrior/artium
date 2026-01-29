'use client';
import '../global.css';

import { Search } from 'lucide-react';
import { motion } from 'framer-motion';

type HeroSectionProps = {
  search: string;
  onSearchChange: (value: string) => void;
  onSearchSubmit?: () => void;
};

export default function HeroSection({
  search,
  onSearchChange,
  onSearchSubmit,
}: HeroSectionProps) {
  return (
    <section className="py-8 md:py-12">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <h1 className="mb-3 text-3xl font-bold md:text-4xl lg:text-5xl">
            Browse Auctions
          </h1>
          <p className="text-muted-foreground">
            Discover original artworks with AI-assisted previews and insights.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mb-8"
        >
          <div className="relative w-full">
            <input
              type="text"
              placeholder="Search your favourite Arts"
              className="search-bar"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') onSearchSubmit?.();
              }}
            />
            <button
              type="button"
              onClick={() => onSearchSubmit?.()}
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg bg-secondary p-2 transition-colors hover:bg-primary hover:text-primary-foreground"
            >
              <Search className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
