/** @type {import('next').NextConfig} */
const nextConfig = {};

// SiteForge's hosted preview serves this site under /preview/<slug>.
// SITEFORGE_BASE_PATH is only set there, never on Vercel. Plain <img> tags
// don't get the basePath automatically, so it's exposed to the asset() helper.
const siteforgeBase = process.env.SITEFORGE_BASE_PATH || "";
export default {
  ...nextConfig,
  ...(siteforgeBase ? { basePath: siteforgeBase } : {}),
  env: { NEXT_PUBLIC_BASE_PATH: siteforgeBase },
};
