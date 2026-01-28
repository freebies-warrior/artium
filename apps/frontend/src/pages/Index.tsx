import Header from "@/components/Header";
import HeroSection from "@/components/HeroSection";
import TopSellers from "@/components/TopSellers";
import BrowseCategories from "@/components/BrowseCategories";
import DiscoverArts from "@/components/DiscoverArts";
import FeaturedAuction from "@/components/FeaturedAuction";
import HowItWorks from "@/components/HowItWorks";
import Newsletter from "@/components/Newsletter";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <HeroSection />
        <TopSellers />
        <BrowseCategories />
        <DiscoverArts />
        <FeaturedAuction />
        <HowItWorks />
        <Newsletter />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
