/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // All data ships as static JSON imported at build time, so the whole app
  // prerenders. No server runtime, no API routes, no env vars required.
};

export default nextConfig;
