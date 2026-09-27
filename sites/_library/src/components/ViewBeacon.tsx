"use client";

import { useEffect } from "react";
import { siteConfig } from "@/lib/content";

/**
 * Tells SiteForge when someone opens this demo, so the operator can see the
 * prospect looked at it. One sendBeacon per browser session, fire-and-forget,
 * no cookies and nothing personal sent. Silent when:
 *   - site.json has no beaconUrl (SITEFORGE_PUBLIC_URL wasn't set at build)
 *   - the page is framed (SiteForge's own preview) or running on localhost
 */
export function ViewBeacon() {
  useEffect(() => {
    const url = siteConfig.beaconUrl;
    if (!url) return;
    let framed = false;
    try {
      framed = window.self !== window.top;
    } catch {
      framed = true;
    }
    const host = window.location.hostname;
    if (framed || host === "localhost" || host === "127.0.0.1") return;
    try {
      if (sessionStorage.getItem("sf-viewed")) return;
      sessionStorage.setItem("sf-viewed", "1");
    } catch {
      /* storage blocked: still send once for this page load */
    }
    const body = JSON.stringify({ slug: siteConfig.slug, path: window.location.pathname, ref: document.referrer || "" });
    try {
      if (!navigator.sendBeacon?.(url, new Blob([body], { type: "text/plain" }))) {
        fetch(url, { method: "POST", body, mode: "no-cors", keepalive: true }).catch(() => {});
      }
    } catch {
      /* never let tracking break the page */
    }
  }, []);
  return null;
}
