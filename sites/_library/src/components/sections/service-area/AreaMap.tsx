"use client";

import dynamic from "next/dynamic";

// maplibre-gl is ~200 kB: load it only on pages that actually show the map,
// and only in the browser. The framed placeholder holds the space meanwhile.
export const AreaMap = dynamic(() => import("./MapInner"), { ssr: false, loading: () => null });
