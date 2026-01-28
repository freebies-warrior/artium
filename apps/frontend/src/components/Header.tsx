import { useState } from "react";
import { Menu, X, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  
  const navLinks = [{
    name: "Painting",
    href: "#"
  }, {
    name: "Sculptures",
    href: "#"
  }, {
    name: "Top Sellers",
    href: "#"
  }];
  
  return <header className="fixed top-0 left-0 right-0 z-50 glass-effect border-b border-border">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="font-display font-bold text-primary-foreground text-sm">A</span>
            </div>
            <span className="font-display font-semibold text-foreground hidden sm:block">Artium</span>
          </div>

          {/* Search Bar */}
          <div className="hidden md:flex items-center flex-1 max-w-md mx-8">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
              <Input
                type="text"
                placeholder="Search arts, artists..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-secondary/50 border-border focus:border-primary"
              />
            </div>
          </div>

          {/* Desktop Navigation + CTA grouped on right */}
          <div className="hidden md:flex items-center gap-4">
            <nav className="flex items-center gap-8">
              {navLinks.map(link => <a key={link.name} href={link.href} className="text-muted-foreground hover:text-foreground transition-colors text-sm font-medium">
                  {link.name}
                </a>)}
            </nav>
            <Button size="sm" className="glow-primary">
              Sign Up
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button className="md:hidden text-foreground" onClick={() => setIsMenuOpen(!isMenuOpen)}>
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMenuOpen && <nav className="md:hidden mt-4 pb-4 border-t border-border pt-4">
            <div className="flex flex-col gap-4">
              {navLinks.map(link => <a key={link.name} href={link.href} className="text-muted-foreground hover:text-foreground transition-colors">
                  {link.name}
                </a>)}
              <Button size="sm" className="w-fit glow-primary">
                Sign Up
              </Button>
            </div>
          </nav>}
      </div>
    </header>;
};
export default Header;