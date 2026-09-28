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

/** credit: photographer attribution (required for Google Places photos) — always shown. */
export type Img = { src: string; alt: string; width?: number; height?: number; caption?: string; credit?: string };
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
    /** icons.tsx key for the oversized outline mark on image-less heroes. */
    icon?: string;
    /** A short standalone quote from a real review, chosen at build time. */
    quote?: { text: string; author: string; rating?: number };
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
  preset: "heritage" | "industrial" | "clean-local" | "bold" | "quote-box" | "van" | "spec-sheet";
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

const QUOTE_OPENERS = new Set(["he", "she", "they", "it", "this", "that", "and", "but", "so", "also", "then", "which", "him", "them", "his", "her", "their", "as", "because", "plus"]);

/**
 * The hero's review quote: content.hero.quote (chosen and trimmed by
 * SiteForge at build time), else the same pick made here — the review whose
 * first sentence stands alone best, cut to 25 words. Keep in step with
 * site_library.hero_quote().
 */
export function heroQuote(maxWords = 25): { text: string; author: string; rating: number; path: string } | null {
  const q = content.hero?.quote;
  if (q?.text && q.author) return { text: q.text, author: q.author, rating: q.rating || 5, path: "hero.quote" };
  let best: { r: (typeof reviewItems)[number]; words: string[]; score: number } | null = null;
  for (const r of reviewItems) {
    const text = r.text.replace(/\s+/g, " ").trim();
    const first = (text.match(/^(.+?[.!?])(\s|$)/)?.[1] || text).trim();
    const words = first.split(" ");
    let score = words.length >= 6 && words.length <= maxWords ? 3 : words.length < 6 ? 1 : 0;
    if (QUOTE_OPENERS.has(words[0].toLowerCase().replace(/[,.]/g, ""))) score -= 3;
    if (/[.!]$/.test(first)) score += 1;
    score += (r.rating || 5) - 5 - Math.abs(words.length - 16) / 20;
    if (!best || score > best.score) best = { r, words: words.length < 6 ? text.split(" ") : words, score };
  }
  if (!best) return null;
  const cut = best.words.length > maxWords;
  const text = best.words.slice(0, maxWords).join(" ").replace(/[,;:—-]+$/, "") + (cut ? "…" : "");
  return { text, author: best.r.author, rating: best.r.rating || 5, path: "" };
}
