"use client";

import { useEffect, useRef } from "react";

/**
 * Only active when this page is running inside an iframe AND the URL has
 * ?edit=1 — i.e. only inside SiteForge's own edit modal preview, never on
 * a real deployed site. Lets the user hover/click a [data-slot] section to
 * scope hotbar edits to just that component, instead of the whole site.
 */
export function EditBridge() {
  const labelRef = useRef<HTMLDivElement | null>(null);
  const selectedRef = useRef<HTMLElement | null>(null);
  const hoveredRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let inIframe = false;
    try {
      inIframe = window.self !== window.top;
    } catch {
      inIframe = true; // cross-origin access throws, which itself means "framed"
    }
    const editMode = inIframe && new URLSearchParams(window.location.search).get("edit") === "1";
    if (!editMode) return;

    const style = document.createElement("style");
    style.textContent = `
      [data-editbridge-hover] { outline: 2px dashed #3b82f6 !important; outline-offset: -2px; cursor: pointer; }
      [data-editbridge-selected] { outline: 2px solid #3b82f6 !important; outline-offset: -2px; }
      .__editbridge-label {
        position: fixed; z-index: 999999; background: #3b82f6; color: #fff;
        font: 600 11px/1.4 -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 2px 8px; border-radius: 4px; pointer-events: none;
        transform: translateY(-100%);
      }
    `;
    document.head.appendChild(style);

    const label = document.createElement("div");
    label.className = "__editbridge-label";
    label.style.display = "none";
    document.body.appendChild(label);
    labelRef.current = label;

    function findSlot(target: EventTarget | null): HTMLElement | null {
      if (!(target instanceof Element)) return null;
      return target.closest("[data-slot]") as HTMLElement | null;
    }

    function positionLabel(el: HTMLElement) {
      const rect = el.getBoundingClientRect();
      const el2 = labelRef.current;
      if (!el2) return;
      el2.textContent = el.getAttribute("data-slot") || "";
      el2.style.display = "block";
      el2.style.left = `${Math.max(0, rect.left)}px`;
      el2.style.top = `${Math.max(0, rect.top)}px`;
    }

    function onMouseOver(e: MouseEvent) {
      const el = findSlot(e.target);
      if (hoveredRef.current && hoveredRef.current !== el) {
        hoveredRef.current.removeAttribute("data-editbridge-hover");
      }
      if (el && el !== selectedRef.current) {
        el.setAttribute("data-editbridge-hover", "");
        positionLabel(el);
        hoveredRef.current = el;
      } else if (!el) {
        hoveredRef.current = null;
      }
    }

    function onMouseOut(e: MouseEvent) {
      const el = findSlot(e.target);
      if (el && el === hoveredRef.current) {
        el.removeAttribute("data-editbridge-hover");
        if (labelRef.current) labelRef.current.style.display = "none";
        hoveredRef.current = null;
      }
    }

    function onClickCapture(e: MouseEvent) {
      const interactive = (e.target as Element)?.closest?.("a, button");
      if (interactive) {
        e.preventDefault();
        e.stopPropagation();
      }
      const el = findSlot(e.target);
      if (!el) return;
      if (selectedRef.current && selectedRef.current !== el) {
        selectedRef.current.removeAttribute("data-editbridge-selected");
      }
      el.removeAttribute("data-editbridge-hover");
      el.setAttribute("data-editbridge-selected", "");
      selectedRef.current = el;
      window.parent.postMessage({ type: "slot-selected", slot: el.getAttribute("data-slot") }, "*");
    }

    function onMessage(e: MessageEvent) {
      if (e.data && e.data.type === "clear-selection" && selectedRef.current) {
        selectedRef.current.removeAttribute("data-editbridge-selected");
        selectedRef.current = null;
      }
    }

    document.addEventListener("mouseover", onMouseOver);
    document.addEventListener("mouseout", onMouseOut);
    document.addEventListener("click", onClickCapture, true);
    window.addEventListener("message", onMessage);

    return () => {
      document.removeEventListener("mouseover", onMouseOver);
      document.removeEventListener("mouseout", onMouseOut);
      document.removeEventListener("click", onClickCapture, true);
      window.removeEventListener("message", onMessage);
      style.remove();
      label.remove();
    };
  }, []);

  return null;
}
