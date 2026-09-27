import type { CSSProperties } from "react";
import brand from "@/brand.json";

// Written by SiteForge's logo editor via src/brand.json:
//   mode   "emblem_text" | "emblem_only" | "text_only"
//   size   emblem height in px (the --logo-size CSS variable)
//   emblem "/brand/emblem.svg" (or .png) — only ever the emblem, never a
//          full logo with its own lettering baked in next to the name.
export function BrandMark({ nameClassName = "" }: { nameClassName?: string }) {
  const showEmblem = brand.mode !== "text_only" && !!brand.emblem;
  const showName = brand.mode !== "emblem_only" || !showEmblem;

  return (
    <span
      data-slot="logo"
      className="inline-flex items-center gap-2.5"
      style={{ "--logo-size": `${brand.size || 36}px` } as CSSProperties}
    >
      {showEmblem && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={brand.emblem}
          alt={showName ? "" : brand.name}
          className="block w-auto shrink-0"
          style={{ height: "var(--logo-size)" }}
        />
      )}
      {showName && (
        <span
          className={nameClassName}
          style={{ fontFamily: "var(--font-heading, var(--font-body)), system-ui, sans-serif" }}
        >
          {brand.name}
        </span>
      )}
    </span>
  );
}
