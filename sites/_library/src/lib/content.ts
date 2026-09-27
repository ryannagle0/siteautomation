import raw from "@/content.json";
import site from "@/site.json";

/**
 * Every word on the page comes from src/content.json. Components read it
 * through this module; the <T> helper in components/T.tsx renders a string
 * by its dotted path and tags it data-edit="<path>" so SiteForge's inline
 * editor writes straight back to that key.
 *
 * Everything below `business` is optional: a section whose content is
 * missing renders nothing rather than an empty shell.
 */

export type Img = { src: string; alt: string; width?: number; height?: number; caption?: string };
export type Link = { label: string; href: string };

export type Content = {
  business: {
    name: string;
    trade?: string;
    town?: string;
    county?: string;
    ownerFirstName?: string;
    phone?: { display: string; tel: string; intl?: string; wa?: string };
    email?: string;
    address?: string;
    hours?: string;
    mapsUrl?: string;
    lat?: number;
    lng?: number;
  };
  seo: { title: string; description: string };
  nav?: { links?: Link[]; cta?: string; note?: string };
  hero?: {
    headline: string;
    subhead?: string;
    primaryCta?: string;
    secondaryCta?: string;
    note?: string;
    image?: Img;
    images?: Img[];
  };
  trust?: { heading?: string; items: { icon?: string; title: string; text?: string }[] };
  services?: {
    heading: string;
    intro?: string;
    items: { icon?: string; title: string; text?: string; points?: string[]; image?: Img }[];
  };
  about?: {
    heading: string;
    body: string[];
    image?: Img;
    signoff?: string;
    facts?: { label: string; value: string }[];
  };
  process?: { heading: string; intro?: string; steps: { title: string; text?: string }[] };
  reviews?: {
    heading: string;
    intro?: string;
    rating?: number;
    count?: number;
    source?: string;
    link?: string;
    linkLabel?: string;
    items: { author: string; rating?: number; text: string; when?: string }[];
  };
  gallery?: { heading: string; intro?: string; images: Img[] };
  area?: { heading: string; intro?: string; towns: string[]; note?: string };
  cta?: { heading: string; text?: string; primary?: string; secondary?: string };
  contact?: {
    heading: string;
    intro?: string;
    formHeading?: string;
    services?: string[];
    submit?: string;
    success?: string;
    labels?: { name?: string; phone?: string; email?: string; service?: string; message?: string };
  };
  footer?: { blurb?: string; legal?: string; credit?: string };
  mobileBar?: { call?: string; whatsapp?: string; quote?: string };
  /** Interface words (button labels, form messages, aria labels). Supports {count}-style placeholders. */
  ui?: Record<string, string>;
};

export type SiteConfig = {
  preset: "heritage" | "industrial" | "clean-local" | "bold";
  slug?: string;
  siteUrl?: string;
  beaconUrl?: string;
};

export const content = raw as unknown as Content;
export const siteConfig = site as SiteConfig;
export const biz = content.business;

/** Value at a dotted path ("services.items.2.title"), or undefined. */
export function get(path: string): unknown {
  let cur: unknown = content;
  for (const key of path.split(".")) {
    if (cur == null || typeof cur !== "object") return undefined;
    cur = (cur as Record<string, unknown>)[key];
  }
  return cur;
}

/** A non-empty trimmed string at `path`, else "". */
export function text(path: string): string {
  const v = get(path);
  return typeof v === "string" ? v.trim() : "";
}

/** An interface string from content.ui, with {placeholders} filled in. */
export function ui(key: string, vars: Record<string, string | number> = {}): string {
  const raw = content.ui?.[key] || "";
  return raw.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? String(vars[k]) : ""));
}

/** Prefix a public/ asset path with the preview base path when needed. */
export function asset(src: string | undefined): string {
  if (!src) return "";
  if (/^(https?:)?\/\//.test(src) || src.startsWith("data:")) return src;
  const base = process.env.NEXT_PUBLIC_BASE_PATH || "";
  return `${base}${src.startsWith("/") ? "" : "/"}${src}`;
}

export const hasImage = (img?: Img | null): img is Img => !!img && !!img.src;

export const phone = biz.phone && biz.phone.tel ? biz.phone : null;
export const telHref = phone ? `tel:${phone.tel}` : "";
export const waHref = phone?.wa ? `https://wa.me/${phone.wa}` : "";
export const mailHref = biz.email ? `mailto:${biz.email}` : "";

/** Where the primary "call" action goes: the phone, else the contact form. */
export const primaryHref = telHref || "#contact";

/** "Naas, Newbridge, Clane and Kildare" style list. */
export function joinTowns(towns: string[], max = 4): string {
  const list = towns.filter(Boolean).slice(0, max);
  if (list.length <= 1) return list[0] || "";
  return `${list.slice(0, -1).join(", ")} and ${list[list.length - 1]}`;
}

export const towns = (content.area?.towns || []).filter(Boolean);

export const reviewItems = (content.reviews?.items || []).filter((r) => r && r.text && r.author);
export const hasReviews = reviewItems.length > 0;
