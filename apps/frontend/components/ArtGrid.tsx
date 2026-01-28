'use client';
import '../global.css';
import { motion } from "framer-motion";

// Import Art images
import artMushroom from "../assets/nft-mushroom.jpg";
import artRobot1 from "../assets/nft-robot-1.jpg";
import artRobot2 from "../assets/nft-robot-2.jpg";
import artBear from "../assets/nft-bear.jpg";
import artDog from "../assets/nft-dog.jpg";
import artRobot3 from "../assets/nft-robot-3.jpg";
import artCherry from "../assets/nft-cherry.jpg";
import artSpace from "../assets/nft-space.jpg";
import artSunset from "../assets/nft-sunset.jpg";
import artDesert from "../assets/nft-desert.jpg";
import artApe from "../assets/nft-ape.jpg";
import artCorgi from "../assets/nft-corgi.jpg";

interface Art {
  id: number;
  name: string;
  creator: string;
  creatorAvatar: string;
  image: string;
  highestBid: string;
  due: string;
}

const arts: Art[] = [
  {
    id: 1,
    name: "Magic Mushroom 0325",
    creator: "Shroomie",
    creatorAvatar: "🍄",
    image: artMushroom.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 2,
    name: "Happy Robot 032",
    creator: "BeKind2Robots",
    creatorAvatar: "🤖",
    image: artRobot1.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 3,
    name: "Happy Robot 024",
    creator: "BeKind2Robots",
    creatorAvatar: "🤖",
    image: artRobot2.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 4,
    name: "Designer Bear",
    creator: "Mr Fox",
    creatorAvatar: "🐻",
    image: artBear.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 5,
    name: "Colorful Dog 0356",
    creator: "Keepitreal",
    creatorAvatar: "🐕",
    image: artDog.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 6,
    name: "Dancing Robot 0312",
    creator: "Robotica",
    creatorAvatar: "🤖",
    image: artRobot3.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 7,
    name: "Cherry Blossom Girl 035",
    creator: "MoonDancer",
    creatorAvatar: "🌸",
    image: artCherry.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 8,
    name: "Space Travel",
    creator: "NebulaKid",
    creatorAvatar: "🚀",
    image: artSpace.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 9,
    name: "Sunset Dimension",
    creator: "Animakid",
    creatorAvatar: "🌅",
    image: artSunset.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 10,
    name: "Desert Walk",
    creator: "Catch 22",
    creatorAvatar: "💀",
    image: artDesert.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 11,
    name: "IceCream Ape 0324",
    creator: "Ice Ape Club",
    creatorAvatar: "🦍",
    image: artApe.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
  {
    id: 12,
    name: "Colorful Dog 0344",
    creator: "PuppyPower",
    creatorAvatar: "🐶",
    image: artCorgi.src,
    highestBid: "1.63 ETH",
    due: "26-02-2026",
  },
];

const ArtCard = ({ art, index }: { art: Art; index: number }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.05 }}
      className="art-card cursor-pointer"
    >
      {/* Image */}
      <div className="aspect-square overflow-hidden">
        <img
          src={art.image}
          alt={art.name}
          className="h-full w-full object-cover transition-transform duration-500 hover:scale-110"
        />
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title */}
        <h3 className="mb-2 font-semibold text-foreground">{art.name}</h3>

        {/* Creator */}
        <div className="mb-4 flex items-center gap-2">
          <span className="text-lg">{art.creatorAvatar}</span>
          <span className="text-sm text-muted-foreground">{art.creator}</span>
        </div>

        {/* Price Info */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-muted-foreground">Highest Bid</p>
            <p className="font-mono text-sm font-medium">{art.highestBid}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">Due</p>
            <p className="font-mono text-sm font-medium">{art.due}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default function ArtGrid() {
  return (
    <section className="py-8">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {arts.map((art, index) => (
            <ArtCard key={art.id} art={art} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
};
