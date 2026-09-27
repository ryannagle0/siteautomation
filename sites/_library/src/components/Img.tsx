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
    </div>
  );
}
