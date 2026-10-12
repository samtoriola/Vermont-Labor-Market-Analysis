/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // A verification build can be sent somewhere other than .next, so it does not
  // overwrite the directory a running dev server is serving from. Without this,
  // building while a dev server is up leaves that server returning 404s for its
  // own chunks -- the page shell loads, nothing hydrates, and a browser check
  // then passes against an empty DOM.
  ...(process.env.NEXT_DIST_DIR ? { distDir: process.env.NEXT_DIST_DIR } : {}),
  // All data ships as static JSON imported at build time, so the whole app
  // prerenders. No server runtime, no API routes, no env vars required.
};

export default nextConfig;
