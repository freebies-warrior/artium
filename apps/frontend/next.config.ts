import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '3eb517ed9cc2a0678c1dca2504694bee.r2.cloudflarestorage.com',
        pathname: '/artium-storage/**',
      },
    ],
  },
}

export default nextConfig
