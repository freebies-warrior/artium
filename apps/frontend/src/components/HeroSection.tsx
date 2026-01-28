import { Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import heroArtwork from "@/assets/hero-artwork.jpg";

const HeroSection = () => {
  const stats = [
    { value: "240k+", label: "Live Auctions" },
    { value: "100k+", label: "Artworks" },
    { value: "240k+", label: "Sellers" },
  ];

  return (
    <section className="pt-24 pb-16 md:pt-32 md:pb-24">
      <div className="container mx-auto px-4">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Content */}
          <div className="space-y-8">
            <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
              Auction Fine Art With{" "}
              <span className="text-gradient">AI Assistance</span>
            </h1>
            <p className="text-muted-foreground text-lg max-w-md">
              Artium Is An Auction-First Art Marketplace Enhanced With AI Tools That Help Buyers Understand Artworks, Preview Them In Their Space, And Discover Similar Pieces.
            </p>
            <div className="flex flex-wrap gap-4">
              <Button size="lg" className="glow-primary">
                <Play className="w-4 h-4 mr-2" />
                Explore Auctions
              </Button>
            </div>

            {/* Stats */}
            <div className="flex gap-8 pt-4">
              {stats.map((stat, index) => (
                <div key={index}>
                  <div className="font-display text-2xl md:text-3xl font-bold text-foreground">
                    {stat.value}
                  </div>
                  <div className="text-muted-foreground text-sm">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Content - Featured Artwork Card */}
          <div className="relative">
            <div className="gradient-border rounded-2xl overflow-hidden glow-card animate-float">
              <img
                src={heroArtwork}
                alt="Space Walking - Featured Artwork"
                className="w-full aspect-square object-cover"
              />
              <div className="p-4 bg-card">
                <h3 className="font-display font-semibold text-lg">Space Walking</h3>
                <div className="flex items-center gap-2 mt-2">
                  <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center">
                    <span className="text-xs">🚀</span>
                  </div>
                  <span className="text-muted-foreground text-sm">Animakid</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
