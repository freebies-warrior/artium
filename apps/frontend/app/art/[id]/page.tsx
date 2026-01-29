'use client'

import { useState } from 'react'
import '../../../global.css'
import Navbar from '@/components/NavBar'
import CountdownTimer from '@/components/CountdownTimer'
import { ArrowRight, Gem } from 'lucide-react'

import Footer from '@/components/Footer'
import ArtGrid from '@/components/ArtGrid'

// Use any asset image; this one is closest to the template hero vibe
import heroNft from '@/assets/nft-hero-1.jpg'
import heroNft2 from '@/assets/nft-ape.jpg'
import BidButton from '@/components/BidButton'
import Lightbox from '@/components/LightBox'
import PreviewButton from '@/components/PreviewButton'

export default function ArtPage() {
  const [isOpen, setIsOpen] = useState(false)
  const [startIndex, setStartIndex] = useState(0)

  const itemImages = [
    { src: heroNft.src, alt: 'The Orbitians - Image 1' },
    { src: heroNft2.src, alt: 'The Orbitians - Image 2' },
  ]

  return (
    <div className="pt-16 min-h-screen bg-background">
      <section>
        <div className="relative w-full aspect-[16/10] lg:aspect-[21/9] overflow-hidden">
          <button
            type="button"
            className="w-full h-full cursor-zoom-in"
            onClick={() => {
              setStartIndex(0) // start from first image
              setIsOpen(true)
            }}
            aria-label="Open image gallery"
          >
            <img
              src={itemImages[0].src}
              alt="The Orbitians - Featured NFT"
              className="w-full h-full object-cover"
            />
          </button>

          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent pointer-events-none" />
          <div className="absolute inset-0 hero-gradient pointer-events-none" />
        </div>
      </section>

      {/* Lightbox */}
      <Lightbox
        images={itemImages}
        initialIndex={startIndex}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />

      {/* NFT Details Section */}
      <section className="container mx-auto px-4 lg:px-6 -mt-8 lg:-mt-16 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-1">
          {/* Left Column - Info */}
          <div className="lg:col-span-2 space-y-6 lg:mt-">
            <div>
              <h1 className="text-3xl lg:text-5xl font-bold mb-2">
                The Orbitians
              </h1>
              <p className="text-muted-foreground">Listed on Sep 30, 2022</p>
            </div>
            {/* Mobile Timer */}
            <div className="lg:hidden">
              <CountdownTimer />
              <BidButton />
            </div>

            {/* Seller Info */}
            <div>
              <p className="text-muted-foreground text-sm mb-2">Seller</p>
              <div className="flex items-center gap-2">
                <Gem className="w-5 h-5 text-primary" />
                <span className="font-medium">Orbitian</span>
              </div>
            </div>

            {/* Description */}
            <div>
              <p className="text-muted-foreground text-sm mb-3">Description</p>
              <div className="space-y-4 text-foreground/90">
                <p>
                  The Orbitians explores isolation, observation, and survival
                  through a futuristic lens.
                </p>
                <p>
                  This piece is part of an experimental series that blends
                  digital illustration with speculative storytelling. The work
                  emphasizes atmosphere and scale, inviting viewers to imagine
                  humanity as both observer and subject.
                </p>
              </div>
            </div>
            <PreviewButton />
          </div>

          {/* Right Column - Timer & Bid (Desktop) */}
          <div className="hidden lg:flex flex-col gap-4">
            <CountdownTimer />
            <BidButton />
          </div>
        </div>
      </section>

      {/* More From Artist Section */}
      <section className="container mx-auto px-4 lg:px-6 mt-16 lg:mt-24">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8 lg:mb-12">
          <h2 className="text-2xl lg:text-3xl font-bold">
            More From This User
          </h2>
          <button className="group inline-flex items-center gap-2 px-4 py-2 border border-purple-800 rounded-lg hover:bg-purple-500/10 transition">
            <ArrowRight className="text-purple-500 w-4 h-4 mr-2 transition-transform group-hover:translate-x-1" />
            Go To User Page
          </button>
        </div>
        <ArtGrid />
      </section>
      <Footer />
    </div>
  )
}
