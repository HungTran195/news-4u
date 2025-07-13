/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['techcrunch.com', 'www.theverge.com', 'feeds.bloomberg.com', 'feeds.finance.yahoo.com', 'www.ft.com', 'feeds.bbci.co.uk', 'feeds.reuters.com'],
  },
  // Removed rewrites() - using NEXT_PUBLIC_API_URL environment variable instead
  // Ensure proper output for Netlify
  trailingSlash: false,
  generateEtags: false,
  // Enable standalone output for Docker
  output: 'standalone',
  // Memory optimization
  swcMinify: true,
  compress: true,
};

module.exports = nextConfig; 