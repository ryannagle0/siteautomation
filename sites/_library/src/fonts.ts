// Fonts for every preset. SiteForge rewrites this file for each built
// site so it only loads (and preloads) the chosen preset's two faces; this
// full version is what the library itself uses to preview every preset.
import {
  Archivo,
  Barlow,
  Big_Shoulders_Display,
  Bricolage_Grotesque,
  Brygada_1918,
  Epilogue,
  Figtree,
  Hanken_Grotesk,
  Inter,
  Libre_Franklin,
  Manrope,
} from "next/font/google";

const brygada = Brygada_1918({ subsets: ["latin"], variable: "--font-brygada", display: "swap", preload: false });
const libreFranklin = Libre_Franklin({ subsets: ["latin"], variable: "--font-libre-franklin", display: "swap", preload: false });
const bigShoulders = Big_Shoulders_Display({ subsets: ["latin"], variable: "--font-big-shoulders", display: "swap", preload: false });
const barlow = Barlow({ subsets: ["latin"], weight: ["400", "500", "600", "700"], variable: "--font-barlow", display: "swap", preload: false });
const bricolage = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-bricolage", display: "swap", preload: false });
const figtree = Figtree({ subsets: ["latin"], variable: "--font-figtree", display: "swap", preload: false });
const epilogue = Epilogue({ subsets: ["latin"], variable: "--font-epilogue", display: "swap", preload: false });
const hanken = Hanken_Grotesk({ subsets: ["latin"], variable: "--font-hanken", display: "swap", preload: false });
// Electrician templates.
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope", display: "swap", preload: false });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap", preload: false });
const archivo = Archivo({ subsets: ["latin"], variable: "--font-archivo", display: "swap", preload: false });

export const FONT_PRESET = "all";
export const fontClassName = [brygada, libreFranklin, bigShoulders, barlow, bricolage, figtree, epilogue, hanken, manrope, inter, archivo]
  .map((f) => f.variable)
  .join(" ");
