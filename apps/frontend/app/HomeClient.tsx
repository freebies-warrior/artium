'use client'
import '../global.css'
import { useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Footer from '@/components/Footer'
import HeroSection from '@/components/HeroSections'
import Tabs from '@/components/Tabs'
import ArtGrid from '@/components/ArtGrid'
import Pagination from '@/components/Pagination'
export default function HomeClient() {
  const [activeTab, setActiveTab] = useState<'arts' | 'sellers'>('arts')
  const [page, setPage] = useState(1)

  const params = useSearchParams()
  const router = useRouter()
  const verifyStatus = params.get('verify')

  const [dismissed, setDismissed] = useState(false)

  let banner: { message: string; type: 'success' | 'error' } | null = null

  if (!dismissed) {
    if (verifyStatus === 'failed') {
      banner = {
        message: 'This verification link is invalid or has expired.',
        type: 'error',
      }
    } else if (verifyStatus === 'success') {
      banner = {
        message:
          'Your email has been verified successfully. You may now log in.',
        type: 'success',
      }
    }
  }

  const totalItems = activeTab === 'arts' ? 302 : 67 // just logic
  const pageSize = 12
  return (
    <div className="min-h-screen bg-background">
      <main className="pt-16">
        {banner && (
          <div className="fixed top-20 left-0 right-0 z-40 flex justify-center px-4">
            <div
              className={`relative w-full max-w-4xl rounded-lg px-4 py-3 text-center shadow
        ${
          banner.type === 'success'
            ? 'bg-green-100 border border-green-300 text-green-700'
            : 'bg-red-100 border border-red-300 text-red-700'
        }`}
            >
              <span>{banner.message}</span>

              <button
                onClick={() => {
                  setDismissed(true)
                  router.replace('/', { scroll: false })
                }}
                className="absolute right-4 top-1/2 -translate-y-1/2 font-bold"
                aria-label="Close banner"
              >
                ×
              </button>
            </div>
          </div>
        )}
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
