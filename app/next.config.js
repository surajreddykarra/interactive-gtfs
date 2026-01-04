/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Set basePath if deploying to a subdirectory
  // basePath: '/hyderabad-transit',
  trailingSlash: true,
};

module.exports = nextConfig;
