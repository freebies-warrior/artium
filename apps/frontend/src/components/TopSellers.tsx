import { TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";

const sellers = [
  { name: "Keepitreal", sales: "34", color: "from-purple-500 to-pink-500" },
  { name: "DigiLab", sales: "34", color: "from-blue-500 to-cyan-500" },
  { name: "GravityOne", sales: "34", color: "from-green-500 to-emerald-500" },
  { name: "Juanie", sales: "34", color: "from-orange-500 to-yellow-500" },
  { name: "BlueWhale", sales: "34", color: "from-blue-600 to-purple-600" },
  { name: "Mr Fox", sales: "34", color: "from-red-500 to-orange-500" },
  { name: "Shroomie", sales: "34", color: "from-pink-500 to-purple-500" },
  { name: "Robotica", sales: "34", color: "from-cyan-500 to-blue-500" },
  { name: "RustyRobot", sales: "34", color: "from-amber-500 to-orange-500" },
  { name: "Animakid", sales: "34", color: "from-violet-500 to-purple-500" },
  { name: "Dotgu", sales: "34", color: "from-rose-500 to-pink-500" },
  { name: "Ghiblier", sales: "34", color: "from-teal-500 to-green-500" },
];

const TopSellers = () => {
  return (
    <section className="py-16 md:py-24">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-12">
          <div>
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-2">Top Sellers</h2>
            <p className="text-muted-foreground">
              Seller With The Highest Sales Performance On Artium Auctions
            </p>
          </div>
          <Button variant="outline" className="gap-2">
            <TrendingUp className="w-4 h-4" />
            View Rankings
          </Button>
        </div>

        {/* Sellers Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {sellers.map((seller, index) => (
            <div
              key={index}
              className="bg-card rounded-xl p-4 hover:bg-card-hover transition-colors group"
            >
              <div className="flex flex-col items-center text-center gap-3">
                <div
                  className={`w-16 h-16 rounded-full bg-gradient-to-br ${seller.color} flex items-center justify-center text-2xl font-bold text-white shadow-lg group-hover:scale-110 transition-transform`}
                >
                  {seller.name.charAt(0)}
                </div>
                <div>
                  <h4 className="font-medium text-foreground text-sm">{seller.name}</h4>
                  <p className="text-muted-foreground text-xs">
                    Artwork Sold: <span className="text-primary">{seller.sales}</span>
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TopSellers;
