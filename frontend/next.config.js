/** @type {import('next').NextConfig} */
const nextConfig = {
  // Memory optimization
  swcMinify: true,
  // Enable standalone output for Docker
  output: 'standalone',
  generateEtags: false,
  async headers() {
    return [
      {
        source: '/',
        headers: [
          { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
        ],
      },
    ];
  },

};

module.exports = nextConfig; 