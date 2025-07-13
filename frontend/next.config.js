/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['techcrunch.com', 'www.theverge.com', 'feeds.bloomberg.com', 'feeds.finance.yahoo.com', 'www.ft.com', 'feeds.bbci.co.uk', 'feeds.reuters.com'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
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