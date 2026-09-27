import type { Metadata, Viewport } from "next";
import "../tokens.css";
import "./globals.css";
import { fontClassName } from "@/fonts";
import { EditBridge } from "@/components/EditBridge";
import { ViewBeacon } from "@/components/ViewBeacon";
import { content, siteConfig, biz } from "@/lib/content";

const SITE_URL = siteConfig.siteUrl || (siteConfig.slug ? `https://${siteConfig.slug}.vercel.app` : "http://localhost:3000");

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: content.seo.title,
  description: content.seo.description,
  alternates: { canonical: "/" },
  openGraph: {
    title: content.seo.title,
    description: content.seo.description,
    url: "/",
    siteName: biz.name,
    locale: "en_IE",
    type: "website",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: biz.name }],
  },
  twitter: { card: "summary_large_image", title: content.seo.title, description: content.seo.description, images: ["/og.png"] },
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

// schema.org type per trade; anything unknown is a generic local business.
const SCHEMA_TYPES: Record<string, string> = {
  electrician: "Electrician",
  plumber: "Plumber",
  "heating engineer": "HVACBusiness",
  roofer: "RoofingContractor",
  painter: "HousePainter",
  builder: "GeneralContractor",
  locksmith: "Locksmith",
  café: "CafeOrCoffeeShop",
  cafe: "CafeOrCoffeeShop",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": SCHEMA_TYPES[(biz.trade || "").toLowerCase()] || "LocalBusiness",
    name: biz.name,
    ...(biz.phone?.intl ? { telephone: biz.phone.intl } : {}),
    ...(biz.email ? { email: biz.email } : {}),
    address: {
      "@type": "PostalAddress",
      ...(biz.town ? { addressLocality: biz.town } : {}),
      ...(biz.county ? { addressRegion: `Co. ${biz.county}` } : {}),
      addressCountry: "IE",
    },
    ...(content.area?.towns?.length ? { areaServed: content.area.towns } : {}),
    ...(content.reviews?.rating && content.reviews?.count
      ? { aggregateRating: { "@type": "AggregateRating", ratingValue: content.reviews.rating, reviewCount: content.reviews.count } }
      : {}),
    url: SITE_URL,
  };

  return (
    <html lang="en-IE" data-preset={siteConfig.preset} className={fontClassName}>
      <head>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      </head>
      <body>
        <EditBridge />
        <ViewBeacon />
        {children}
      </body>
    </html>
  );
}
