"use client";

import { useState, type FormEvent } from "react";
import { ArrowRight } from "lucide-react";
import { requestQuote } from "@/components/ContactForm";
import { cn } from "@/lib/cn";

/**
 * The quick-quote hero's focal point: one line to describe the job, service
 * chips to tap, and a send button that carries both into the page's quote
 * form (prefilled) — the first screen becomes the start of the request.
 */
export function QuickQuote({
  label,
  placeholder,
  submit,
  services,
  className,
}: {
  label: string;
  placeholder: string;
  submit: string;
  services: string[];
  className?: string;
}) {
  const [text, setText] = useState("");
  const [chosen, setChosen] = useState<string | null>(null);
  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    requestQuote({ service: chosen || undefined, message: text.trim() || undefined });
  };
  return (
    <form onSubmit={onSubmit} className={cn("rounded-theme-lg border-theme border-line bg-surface p-3 md:p-4", className)}>
      <label htmlFor="qq-text" className="t-label block px-1 pb-2 text-ink">{label}</label>
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          id="qq-text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
          autoComplete="off"
          className="field min-h-[3.25rem] flex-1 bg-bg"
        />
        <button type="submit" className="btn btn-primary btn-lg shrink-0">
          {submit}
          <ArrowRight aria-hidden="true" strokeWidth={2} />
        </button>
      </div>
      {services.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label={label}>
          {services.slice(0, 5).map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={chosen === s}
              onClick={() => setChosen(chosen === s ? null : s)}
              className={cn(
                "inline-flex min-h-11 items-center rounded-btn border-theme px-3.5 text-step-small font-medium transition-colors",
                chosen === s ? "border-accent bg-accent text-accent-fg" : "border-line bg-bg text-ink hover:border-accent-line",
              )}
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </form>
  );
}
