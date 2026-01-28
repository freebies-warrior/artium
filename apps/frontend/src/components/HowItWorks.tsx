import { UserPlus, ImagePlus, Sparkles } from "lucide-react";

const steps = [
  {
    icon: UserPlus,
    title: "Setup Your Account",
    description: "Register As A Seller Or Bidder With Just Your Email Address",
    color: "from-purple-500 to-violet-600",
  },
  {
    icon: ImagePlus,
    title: "Explore Or List Art",
    description: "Browse The Auction Or List Your Pieces For Bidding",
    color: "from-pink-500 to-rose-600",
  },
  {
    icon: Sparkles,
    title: "Bid With AI Support",
    description: "Preview Artwork In Your Space, Check Value Trends, And Bid With Confidence",
    color: "from-blue-500 to-cyan-600",
  },
];

const HowItWorks = () => {
  return (
    <section className="py-16 md:py-24">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
            How It Works
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Find Out How To Get Started
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {steps.map((step, index) => (
            <div
              key={index}
              className="bg-card rounded-2xl p-8 text-center group hover:glow-card transition-shadow duration-300"
            >
              <div
                className={`w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}
              >
                <step.icon className="w-10 h-10 text-white" />
              </div>
              <h3 className="font-display font-semibold text-xl mb-3">
                {step.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
