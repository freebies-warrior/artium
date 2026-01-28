'use client';
import "../global.css";
import { useState } from "react";
import Footer from "@/components/Footer"
import HeroSection from "@/components/HeroSections";
import Tabs from "@/components/Tabs";
import ArtGrid from "@/components/ArtGrid";
export default function Home() {
  const [activeTab, setActiveTab] = useState<"arts" | "sellers">("arts");

  return (
    <div className="min-h-screen bg-background">
      <main>
        <HeroSection />
        <Tabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          artsCount={302}
          sellersCount={67}
        />
        <ArtGrid />
      </main>
      <Footer />
    </div>
  )
}
