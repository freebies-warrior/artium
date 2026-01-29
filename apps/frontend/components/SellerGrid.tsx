'use client';

import "../global.css";
import { motion } from "framer-motion";

type Seller = {
  id: number;
  name: string;
  username: string;
  avatarLetter: string;
  items: number;
  volume: string; // keep as string like "12.4 ETH"
};

const sellers: Seller[] = [
  { id: 1, name: "Shroomie", username: "@shroomie", avatarLetter: "S", items: 58, volume: "124.7 ETH" },
  { id: 2, name: "BeKind2Robots", username: "@bekind2robots", avatarLetter: "B", items: 44, volume: "98.2 ETH" },
  { id: 3, name: "Mr Fox", username: "@mrfox", avatarLetter: "M", items: 31, volume: "75.9 ETH" },
  { id: 4, name: "Keepitreal", username: "@keepitreal", avatarLetter: "K", items: 29, volume: "63.1 ETH" },
  { id: 5, name: "Robotica", username: "@robotica", avatarLetter: "R", items: 27, volume: "59.8 ETH" },
  { id: 6, name: "MoonDancer", username: "@moondancer", avatarLetter: "M", items: 23, volume: "51.4 ETH" },
  { id: 7, name: "NebulaKid", username: "@nebulakid", avatarLetter: "N", items: 21, volume: "49.2 ETH" },
  { id: 8, name: "Animakid", username: "@animakid", avatarLetter: "A", items: 18, volume: "42.7 ETH" },
  { id: 9, name: "Catch 22", username: "@catch22", avatarLetter: "C", items: 16, volume: "37.0 ETH" },
];

function SellerCard({ seller, index }: { seller: Seller; index: number }) {
  return (
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
  );
}

export default function SellerGrid() {
  return (
    <section className="py-8">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {sellers.map((seller, index) => (
            <SellerCard key={seller.id} seller={seller} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}
