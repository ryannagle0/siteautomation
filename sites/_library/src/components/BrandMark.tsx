import type { CSSProperties } from "react";
import brand from "@/brand.json";
import { asset } from "@/lib/content";

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
      className="inline-flex min-w-0 items-center gap-2.5"
      style={{ "--logo-size": `${brand.size || 36}px` } as CSSProperties}
    >
      {showEmblem && (
        <img
          src={asset(brand.emblem)}
          alt={showName ? "" : brand.name}
          className="block w-auto shrink-0"
          style={{ height: "var(--logo-size)" }}
        />
      )}
      {showName && (
        <span
          data-edit="business.name"
          className={nameClassName}
          style={{ fontFamily: "var(--font-display)", fontWeight: "var(--display-weight)" as CSSProperties["fontWeight"],
            letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)" as CSSProperties["textTransform"] }}
        >
          {brand.name}
        </span>
      )}
    </span>
  );
}
