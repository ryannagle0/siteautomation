import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type Tone = "base" | "surface" | "band" | "accent";

/**
 * Root of every section variant: the data-slot marker SiteForge's editor
 * uses to scope edits, the anchor id, and the tone (background world).
 */
export function Section({
  slot,
  tone = "base",
  id,
  className,
  children,
  as: Tag = "section",
  label,
}: {
  slot: string;
  tone?: Tone;
  id?: string;
  className?: string;
  children: ReactNode;
  as?: "section" | "header" | "footer" | "div";
  label?: string;
}) {
  return (
    <Tag data-slot={slot} data-tone={tone} id={id} aria-label={label} className={cn("relative", className)}>
      {children}
    </Tag>
  );
}
