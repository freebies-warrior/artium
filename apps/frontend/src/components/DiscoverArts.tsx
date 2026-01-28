import { Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import artGalaxy from "@/assets/art-galaxy.jpg";
import artEdena from "@/assets/art-edena.jpg";
import artAstrofiction from "@/assets/art-astrofiction.jpg";

const artworks = [
  {
    title: "Distant Galaxy",
    artist: "MoonDancer",
    price: "1.63 ETH",
    highestBid: "0.33 wETH",
    image: artGalaxy,
  },
  {
    title: "Life On Edena",
    artist: "NebulaKid",
    price: "1.63 ETH",
    highestBid: "0.33 wETH",
    image: artEdena,
  },
  {
    title: "AstroFiction",
    artist: "Spaceone",
    price: "1.63 ETH",
    highestBid: "0.33 wETH",
    image: artAstrofiction,
  },
];

const DiscoverArts = () => {
  return (
    <section className="py-16 md:py-24">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-12">
          <div>
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-2">
              Discover More Arts
            </h2>
            <p className="text-muted-foreground">Explore New Trending Arts</p>
          </div>
          <Button variant="outline" className="gap-2">
            <Eye className="w-4 h-4" />
            See All
          </Button>
        </div>

        {/* Arts Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {artworks.map((artwork, index) => (
            <div
              key={index}
              className="bg-card rounded-2xl overflow-hidden group hover:glow-card transition-shadow duration-300"
            >
              <div className="relative overflow-hidden">
                <img
                  src={artwork.image}
                  alt={artwork.title}
                  className="w-full aspect-square object-cover group-hover:scale-105 transition-transform duration-500"
                />
              </div>
              <div className="p-5">
                <h3 className="font-display font-semibold text-lg mb-2">
                  {artwork.title}
                </h3>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                    <span className="text-xs font-bold text-primary-foreground">
                      {artwork.artist.charAt(0)}
                    </span>
                  </div>
                  <span className="text-muted-foreground text-sm">{artwork.artist}</span>
                </div>
                <div className="flex justify-between items-center pt-4 border-t border-border">
                  <div>
                    <p className="text-xs text-muted-foreground">Price</p>
                    <p className="font-medium text-foreground">{artwork.price}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Highest Bid</p>
                    <p className="font-medium text-foreground">{artwork.highestBid}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default DiscoverArts;
