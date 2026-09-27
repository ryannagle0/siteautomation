"use client";

import { useEffect, useRef } from "react";

/**
 * Only active when this page is running inside an iframe AND the URL has
 * ?edit=1 — i.e. only inside SiteForge's own edit modal preview, never on
 * a real deployed site. Lets the user hover/click a [data-slot] section to
 * scope hotbar edits to just that component, and double-click text to edit
 * it in place.
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
      [data-editbridge-target] { outline: 3px solid #f59e0b !important; outline-offset: -3px; box-shadow: inset 0 0 0 9999px rgba(245,158,11,.08); }
      [data-editbridge-editing] { outline: 2px solid rgba(59,130,246,.55) !important; outline-offset: 3px; border-radius: 2px; cursor: text; }
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
      const r = el.getBoundingClientRect();
      window.parent.postMessage(
        {
          type: "slot-selected",
          slot: el.getAttribute("data-slot"),
          rect: { x: r.left, y: r.top, width: r.width, height: r.height },
        },
        "*",
      );
    }

    // ---- Inline text editing: double-click text, Enter/click-away saves,
    // Escape cancels. Library sites tag every text node with
    // data-edit="<content.json path>", so the edit goes straight to that key.
    // Older sites fall back to elements whose children are all text nodes.
    const TEXT_SELECTOR = "h1,h2,h3,h4,h5,h6,p,span,a,li,button";
    let editing: { el: HTMLElement; original: string; slot: string; path: string } | null = null;

    function editableTarget(target: EventTarget | null): HTMLElement | null {
      if (!(target instanceof Element)) return null;
      const tagged = target.closest("[data-edit]") as HTMLElement | null;
      if (tagged && tagged.closest("[data-slot]")) {
        const nodes = Array.from(tagged.childNodes);
        const textOnly = nodes.length > 0 && nodes.every((n) => n.nodeType === Node.TEXT_NODE);
        return textOnly && (tagged.textContent || "").trim() ? tagged : null;
      }
      const el = target.closest(TEXT_SELECTOR) as HTMLElement | null;
      if (!el || !el.closest("[data-slot]")) return null;
      const nodes = Array.from(el.childNodes);
      if (!nodes.length || !nodes.every((n) => n.nodeType === Node.TEXT_NODE)) return null;
      return (el.textContent || "").trim() ? el : null;
    }

    function finishEdit(save: boolean) {
      const cur = editing;
      if (!cur) return;
      editing = null;
      const { el, original, slot, path } = cur;
      el.removeEventListener("keydown", onEditKey);
      el.removeEventListener("blur", onEditBlur);
      el.removeAttribute("contenteditable");
      el.removeAttribute("data-editbridge-editing");
      const oldText = original.replace(/\s+/g, " ").trim();
      const newText = (el.textContent || "").replace(/\s+/g, " ").trim();
      if (!save || !newText || newText === oldText) {
        el.textContent = original;
        return;
      }
      window.parent.postMessage({ type: "text-edit", slot, path, oldText, newText }, "*");
    }

    function onEditKey(e: KeyboardEvent) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        finishEdit(true);
      } else if (e.key === "Escape") {
        e.preventDefault();
        finishEdit(false);
      }
    }

    function onEditBlur() {
      finishEdit(true);
    }

    function onDblClick(e: MouseEvent) {
      if (editing) return;
      const el = editableTarget(e.target);
      if (!el) return;
      e.preventDefault();
      editing = {
        el,
        original: el.textContent || "",
        slot: el.closest("[data-slot]")!.getAttribute("data-slot") || "",
        path: el.getAttribute("data-edit") || "",
      };
      el.setAttribute("data-editbridge-editing", "");
      try {
        el.contentEditable = "plaintext-only";
      } catch {
        el.contentEditable = "true"; // browsers without plaintext-only support
      }
      el.addEventListener("keydown", onEditKey);
      el.addEventListener("blur", onEditBlur);
      el.focus();
      const range = document.createRange();
      range.selectNodeContents(el);
      const sel = window.getSelection();
      sel?.removeAllRanges();
      sel?.addRange(range);
    }

    // Section the dashboard's component drawer would replace (hovering a card).
    let targetEl: HTMLElement | null = null;
    function highlightSlot(slot: string | null) {
      if (targetEl) targetEl.removeAttribute("data-editbridge-target");
      targetEl = slot ? (document.querySelector(`[data-slot="${CSS.escape(slot)}"]`) as HTMLElement | null) : null;
      if (!targetEl) return;
      targetEl.setAttribute("data-editbridge-target", "");
      const rect = targetEl.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) {
        targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }

    function onMessage(e: MessageEvent) {
      if (!e.data) return;
      if (e.data.type === "clear-selection" && selectedRef.current) {
        selectedRef.current.removeAttribute("data-editbridge-selected");
        selectedRef.current = null;
      } else if (e.data.type === "list-slots") {
        const slots = Array.from(document.querySelectorAll("[data-slot]"))
          .map((el) => el.getAttribute("data-slot") || "")
          .filter((s, i, all) => s && all.indexOf(s) === i);
        window.parent.postMessage({ type: "slots", slots }, "*");
      } else if (e.data.type === "highlight-slot") {
        highlightSlot(e.data.slot || null);
      }
    }

    // H (outside text editing) asks the dashboard to hide/show its hotbar,
    // so the shortcut works while the preview has keyboard focus too.
    function onKeyDown(e: KeyboardEvent) {
      if (editing || e.ctrlKey || e.metaKey || e.altKey) return;
      const t = e.target as HTMLElement | null;
      if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
      if (e.key === "h" || e.key === "H") {
        e.preventDefault();
        window.parent.postMessage({ type: "toggle-hotbar" }, "*");
      }
    }

    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("mouseover", onMouseOver);
    document.addEventListener("mouseout", onMouseOut);
    document.addEventListener("click", onClickCapture, true);
    document.addEventListener("dblclick", onDblClick);
    window.addEventListener("message", onMessage);

    return () => {
      finishEdit(false);
      highlightSlot(null);
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("mouseover", onMouseOver);
      document.removeEventListener("mouseout", onMouseOut);
      document.removeEventListener("click", onClickCapture, true);
      document.removeEventListener("dblclick", onDblClick);
      window.removeEventListener("message", onMessage);
      style.remove();
      label.remove();
    };
  }, []);

  return null;
}
