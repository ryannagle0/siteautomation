"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MenuIcon, CloseIcon } from "./icons";

const LINKS = [
  { href: "#services", label: "Services" },
  { href: "#about", label: "About" },
  { href: "#process", label: "Process" },
  { href: "#reviews", label: "Reviews" },
  { href: "#contact", label: "Contact" },
];

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <header
        className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
          scrolled || open
            ? "bg-base/95 backdrop-blur border-b border-grey-line"
            : "border-b border-transparent"
        }`}
      >
        <div className="mx-auto flex max-w-content items-center justify-between px-6 py-4 lg:px-10">
          <a href="#top" className="flex items-center gap-2.5">
            <span
              className={`text-[15px] font-semibold tracking-tightest ${
                scrolled || open ? "text-navy" : "text-navy"
              }`}
            >
              {{BUSINESS_NAME}}
            </span>
          </a>

          <nav className="hidden items-center gap-9 lg:flex">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-[13px] font-medium uppercase tracking-wide text-navy/70 transition-colors hover:text-blue"
              >
                {l.label}
              </a>
            ))}
          </nav>

          <div className="hidden items-center gap-5 lg:flex">
            <a
              href="tel:{{PHONE_TEL}}"
              className="num-tabular text-[13px] font-medium text-navy/60"
            >
              {{PHONE_DISPLAY}}
            </a>
            <a
              href="#contact"
              className="rounded-sharp bg-blue px-4 py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-blue-dark"
            >
              Free Quote
            </a>
          </div>

          <button
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            className="flex h-9 w-9 items-center justify-center text-navy lg:hidden"
          >
            {open ? <CloseIcon /> : <MenuIcon />}
          </button>
        </div>
      </header>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="fixed inset-0 z-40 flex flex-col justify-center gap-8 bg-navy px-8 lg:hidden"
          >
            {LINKS.map((l, i) => (
              <motion.a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * i, duration: 0.35 }}
                className="text-3xl font-semibold tracking-tightest text-white"
              >
                {l.label}
              </motion.a>
            ))}
            <motion.a
              href="tel:{{PHONE_TEL}}"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.35 }}
              className="mt-4 inline-block w-fit rounded-sharp bg-blue px-6 py-3 text-sm font-semibold text-white"
            >
              Call {{PHONE_DISPLAY}}
            </motion.a>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
