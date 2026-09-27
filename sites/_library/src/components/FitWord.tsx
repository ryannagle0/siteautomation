"use client";

import { useLayoutEffect, useRef, type CSSProperties } from "react";

/**
 * One line of display type sized to exactly fill its container's width.
 * Renders with a length-based estimate on the server, then measures the
 * real glyph widths (any font, any name length) and corrects on the client.
 */
export function FitWord({ text, max = 240, min = 40, className, style, ...rest }: {
  text: string;
  max?: number;
  /** Below this size a single line stops reading as a poster: wrap instead. */
  min?: number;
  className?: string;
  style?: CSSProperties;
} & Record<`data-${string}`, string>) {
  const ref = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = ref.current;
    const box = el?.parentElement;
    if (!el || !box) return;
    // The reduced-motion rule gives every element a tiny transition; a
    // transitioned font-size would be read before it lands.
    el.style.setProperty("transition", "none", "important");
    const fit = () => {
      // Glyph widths don't scale perfectly linearly (hinting, rounding), so
      // measure at 100px, scale, then correct once more at the target size.
      let size = 100;
      el.style.whiteSpace = "nowrap";
      el.style.width = "max-content";
      for (let pass = 0; pass < 3; pass++) {
        el.style.fontSize = `${size}px`;
        const w = el.getBoundingClientRect().width;
        if (!w) return;
        size = Math.min(max, (size * box.clientWidth) / w);
      }
      const wrap = size < min;
      el.style.fontSize = `${wrap ? min : Math.floor(size * 10) / 10}px`;
      el.style.whiteSpace = wrap ? "normal" : "nowrap";
      el.style.width = wrap ? "auto" : "max-content";
      el.style.height = wrap ? "auto" : (style?.height as string) || "";
    };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(box);
    document.fonts?.ready.then(fit);
    return () => ro.disconnect();
  }, [text, max, min, style?.height]);
  const chars = Math.max(6, Math.min(40, text.length));
  return (
    <div ref={ref} className={className} {...rest}
      style={{ whiteSpace: "nowrap", width: "max-content", fontSize: `min(calc((100vw - 2 * var(--gutter)) / (${chars} * 0.62)), ${max}px)`, ...style }}>
      {text}
    </div>
  );
}
