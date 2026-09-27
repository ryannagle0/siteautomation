import { asset, type Img as ImgT } from "@/lib/content";
import { cn } from "@/lib/cn";

/** A content.json image inside an aspect-ratio frame (`.media`). */
export function Img({
  img,
  className,
  ratio = "4 / 3",
  priority = false,
  sizes,
}: {
  img: ImgT;
  className?: string;
  ratio?: string | null;
  priority?: boolean;
  sizes?: string;
}) {
  return (
    <div className={cn("media", className)} style={ratio ? { aspectRatio: ratio } : undefined}>
      <img
        src={asset(img.src)}
        alt={img.alt || ""}
        width={img.width}
        height={img.height}
        sizes={sizes}
        loading={priority ? "eager" : "lazy"}
        decoding="async"
        {...(priority ? { fetchPriority: "high" as const } : {})}
      />
      {img.credit && <PhotoCredit text={img.credit} />}
    </div>
  );
}

/** Photographer attribution over the photo's corner (Google Places requires it to be visible). */
export function PhotoCredit({ text }: { text: string }) {
  return (
    <span className="absolute bottom-2 right-2 z-10 max-w-[80%] truncate rounded-theme px-2 py-0.5 text-step--2 leading-tight"
      style={{ background: "var(--scrim-mid)", color: "var(--on-scrim)" }}>
      {text}
    </span>
  );
}
