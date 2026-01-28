import { useState, useEffect } from "react";
import { Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import featuredMushrooms from "@/assets/featured-mushrooms.jpg";

const FeaturedAuction = () => {
  const [timeLeft, setTimeLeft] = useState({
    hours: 59,
    minutes: 59,
    seconds: 59,
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev.seconds > 0) {
          return { ...prev, seconds: prev.seconds - 1 };
        } else if (prev.minutes > 0) {
          return { ...prev, minutes: prev.minutes - 1, seconds: 59 };
        } else if (prev.hours > 0) {
          return { hours: prev.hours - 1, minutes: 59, seconds: 59 };
        }
        return prev;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatNumber = (num: number) => num.toString().padStart(2, "0");

  return (
    <section className="py-16 md:py-24">
      <div className="container mx-auto px-4">
        <div className="relative rounded-3xl overflow-hidden">
          {/* Background Image */}
          <img
            src={featuredMushrooms}
            alt="Magic Mushrooms - Featured Auction"
            className="w-full h-[500px] md:h-[600px] object-cover"
          />
          
          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent" />
          
          {/* Content */}
          <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-12">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
              {/* Left Content */}
              <div className="space-y-4">
                <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-card/80 backdrop-blur-sm text-sm">
                  🍄 Shroomie
                </span>
                <h2 className="font-display text-3xl md:text-5xl font-bold">
                  Magic Mushrooms
                </h2>
                <Button className="gap-2 glow-primary">
                  <Eye className="w-4 h-4" />
                  See Art
                </Button>
              </div>

              {/* Countdown Timer */}
              <div className="glass-effect rounded-2xl p-6 md:p-8">
                <p className="text-muted-foreground text-sm mb-4">Auction ends in:</p>
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <div className="font-display text-4xl md:text-5xl font-bold text-foreground animate-countdown">
                      {formatNumber(timeLeft.hours)}
                    </div>
                    <p className="text-muted-foreground text-xs mt-1">Hours</p>
                  </div>
                  <span className="font-display text-4xl md:text-5xl font-bold text-primary">:</span>
                  <div className="text-center">
                    <div className="font-display text-4xl md:text-5xl font-bold text-foreground">
                      {formatNumber(timeLeft.minutes)}
                    </div>
                    <p className="text-muted-foreground text-xs mt-1">Minutes</p>
                  </div>
                  <span className="font-display text-4xl md:text-5xl font-bold text-primary">:</span>
                  <div className="text-center">
                    <div className="font-display text-4xl md:text-5xl font-bold text-foreground">
                      {formatNumber(timeLeft.seconds)}
                    </div>
                    <p className="text-muted-foreground text-xs mt-1">Seconds</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeaturedAuction;
