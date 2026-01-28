import { Twitter, Instagram, Youtube, Github } from "lucide-react";

const Footer = () => {
  const exploreLinks = [
    { name: "Paintings", href: "#" },
    { name: "Sculptures", href: "#" },
    { name: "Top Sellers", href: "#" },
  ];

  const socialLinks = [
    { icon: Twitter, href: "#" },
    { icon: Instagram, href: "#" },
    { icon: Youtube, href: "#" },
    { icon: Github, href: "#" },
  ];

  return (
    <footer className="border-t border-border py-12 md:py-16">
      <div className="container mx-auto px-4">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          {/* Brand */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="font-display font-bold text-primary-foreground text-sm">A</span>
              </div>
              <span className="font-display font-semibold text-foreground">
                Artium
              </span>
            </div>
            <p className="text-muted-foreground max-w-sm">
              AI-assisted art auction platform for paintings and sculptures.
            </p>
            <div className="flex gap-3">
              {socialLinks.map((social, index) => (
                <a
                  key={index}
                  href={social.href}
                  className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>

          {/* Explore */}
          <div>
            <h4 className="font-display font-semibold mb-4">Explore</h4>
            <ul className="space-y-3">
              {exploreLinks.map((link, index) => (
                <li key={index}>
                  <a
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter CTA */}
          <div>
            <h4 className="font-display font-semibold mb-4">Stay Updated</h4>
            <p className="text-muted-foreground text-sm">
              Get the latest about new auctions, trending artworks, and featured sellers.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
