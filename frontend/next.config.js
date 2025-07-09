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
};

module.exports = nextConfig; 