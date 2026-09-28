"use client";

import type { ReactNode } from "react";
import { requestQuote } from "@/components/ContactForm";
import { cn } from "@/lib/cn";

/** One tappable cell of the services table: asks for a quote for that service. */
export function ServiceCell({ service, className, children }: { service: string; className?: string; children: ReactNode }) {
  return (
    <button type="button" onClick={() => requestQuote({ service })}
      className={cn("group flex flex-col text-left transition-colors hover:bg-accent-soft", className)}>
      {children}
    </button>
  );
}
