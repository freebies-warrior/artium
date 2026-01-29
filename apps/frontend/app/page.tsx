'use client'
import '../global.css'
import { useState } from 'react'
import Footer from '@/components/Footer'
import HeroSection from '@/components/HeroSections'
import Tabs from '@/components/Tabs'
import ArtGrid from '@/components/ArtGrid'
import Navbar from '@/components/NavBar'
import Pagination from '@/components/Pagination'
export default function Home() {
  const [activeTab, setActiveTab] = useState<'arts' | 'sellers'>('arts')
  const [page, setPage] = useState(1)

  const totalItems = activeTab === 'arts' ? 302 : 67 // just logic
  const pageSize = 12
  return (
    <div className="min-h-screen bg-background">
      <main className="pt-16">
        <HeroSection />
        <Tabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          artsCount={302}
          sellersCount={67}
        />
        <ArtGrid />
        <div className="container mx-auto px-4 pb-8">
          <Pagination
            page={page}
            totalItems={totalItems}
            pageSize={pageSize}
            onPageChange={setPage}
          />
        </div>
      </main>
      <Footer />
    </div>
  )
}
