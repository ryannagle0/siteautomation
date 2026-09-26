import type { Metadata } from "next";
import "./globals.css";
import { fontClassName, fontStyle, fontStylesheet } from "@/fonts";
import { EditBridge } from "@/components/EditBridge";

const SITE_URL = "https://{{SLUG}}.vercel.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "{{BUSINESS_NAME}} | Electrician {{TOWN}} | Safe Electric Registered",
  description:
    "Safe Electric registered electricians with 20+ years experience serving {{TOWN}}. Domestic rewires, EV chargers, solar panels and 24/7 emergency callout. Call {{OWNER_FIRST_NAME}}: {{PHONE_DISPLAY}}",
  alternates: {
    canonical: SITE_URL,
  },
  openGraph: {
    title: "{{BUSINESS_NAME}} | Electrician {{TOWN}} | Safe Electric Registered",
    description:
      "Safe Electric registered electricians with 20+ years experience serving {{TOWN}}. Domestic rewires, EV chargers, solar panels and 24/7 emergency callout. Call {{OWNER_FIRST_NAME}}: {{PHONE_DISPLAY}}",
    url: SITE_URL,
    siteName: "{{BUSINESS_NAME}}",
    locale: "en_IE",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "{{BUSINESS_NAME}} | Electrician {{TOWN}} | Safe Electric Registered",
    description:
      "Safe Electric registered electricians with 20+ years experience serving {{TOWN}}. Domestic rewires, EV chargers, solar panels and 24/7 emergency callout. Call {{OWNER_FIRST_NAME}}: {{PHONE_DISPLAY}}",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Electrician",
    name: "{{BUSINESS_NAME}}",
    telephone: "{{PHONE_INTL}}",
    email: "{{EMAIL}}",
    address: {
      "@type": "PostalAddress",
      addressLocality: "{{TOWN}}",
      addressRegion: "{{TOWN}}",
      addressCountry: "IE",
    },
    areaServed: ["{{TOWN}}"],
    url: SITE_URL,
    slogan: "20 years experience. Zero shortcuts.",
  };

  return (
    <html lang="en-IE" className={fontClassName} style={fontStyle as React.CSSProperties}>
      <head>
        {fontStylesheet && <link rel="stylesheet" href={fontStylesheet} />}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="font-sans antialiased">
        <EditBridge />
        {children}
      </body>
    </html>
  );
}
