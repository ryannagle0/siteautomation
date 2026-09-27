import type { ElementType, ReactNode } from "react";
import { text } from "@/lib/content";

/**
 * Renders the string at `k` in content.json, tagged data-edit="<k>" so the
 * SiteForge editor maps a double-clicked word straight back to its key.
 * Renders nothing when the key is missing or empty.
 */
export function T({
  k,
  as: Tag = "span",
  className,
  fallback,
  children,
}: {
  k: string;
  as?: ElementType;
  className?: string;
  fallback?: string;
  children?: (value: string) => ReactNode;
}) {
  const value = text(k) || fallback || "";
  if (!value) return null;
  return (
    <Tag data-edit={k} className={className}>
      {children ? children(value) : value}
    </Tag>
  );
}
