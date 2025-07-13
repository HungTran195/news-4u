/** @type {import('next').NextConfig} */
const nextConfig = {
  // Memory optimization
  swcMinify: true,
  // Enable standalone output for Docker
  output: 'standalone',
  generateEtags: false,
};

module.exports = nextConfig; 