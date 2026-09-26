// Written by SiteForge's theme panel — choose a different font there to replace this file.
import { Inter } from "next/font/google";

const font = Inter({ subsets: ["latin"], variable: "--font-body", display: "swap" });

export const FONT_PRESET = "inter";
export const fontClassName = font.variable;
export const fontStyle: Record<string, string> = {};
export const fontStylesheet: string | null = null;
