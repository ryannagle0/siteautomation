/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "maps.googleapis.com",
      },
    ],
  },
};

// SiteForge's hosted preview serves this site under /preview/<slug>.
// SITEFORGE_BASE_PATH is only set there, never on Vercel.
const siteforgeBase = process.env.SITEFORGE_BASE_PATH;
export default siteforgeBase
  ? { ...nextConfig, basePath: siteforgeBase, images: { ...(nextConfig.images || {}), unoptimized: true } }
  : nextConfig;
