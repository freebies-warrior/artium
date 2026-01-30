'use client'

import ArtGrid from '@/components/ArtGrid'
import UserHeader from './components/UserHeader'
import UserStats from './components/UserStats'
import Pagination from '@/components/Pagination'

import { useState } from 'react'

export default function UserClient() {
  const [page, setPage] = useState(1)

  // later these come from backend
  const totalItems = 24 // example: user has 24 listings
  const pageSize = 12
  // later: fetch user + listings here
  return (
    <div className="min-h-screen bg-background pt-20">
      <div className="container mx-auto px-6">
        <UserHeader />
        <UserStats />
        <ArtGrid />

        {/* Pagination */}
        <div className="mt-8 flex justify-center">
          <Pagination
            page={page}
            totalItems={totalItems}
            pageSize={pageSize}
            onPageChange={setPage}
          />
        </div>
      </div>
    </div>
  )
}
