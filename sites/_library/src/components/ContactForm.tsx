"use client";

import { useId, useState, type FormEvent } from "react";
import { ChevronDown } from "lucide-react";
import { MorphingSquare } from "@/components/ui/morphing-square";
import { cn } from "@/lib/cn";

export type FormText = {
  heading?: string;
  submit: string;
  success: string;
  sending: string;
  required: string;
  unavailable: string;
  error: string;
  optional: string;
  labels: { name: string; phone: string; email: string; service: string; message: string };
  services: string[];
  telHref: string;
  phoneDisplay: string;
};

/**
 * Quote form. Posts to /api/contact (Resend). If the site has no email
 * delivery set up, it says so and points to the phone rather than
 * pretending the message went.
 */
export function ContactForm({ t, className }: { t: FormText; className?: string }) {
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [message, setMessage] = useState("");
  const uid = useId();
  const id = (f: string) => `cf-${f}-${uid}`;

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(e.currentTarget).entries());
    if (!String(data.name || "").trim() || (!String(data.phone || "").trim() && !String(data.email || "").trim())) {
      setStatus("error");
      setMessage(t.required);
      return;
    }
    setStatus("sending");
    setMessage("");
    try {
      const base = process.env.NEXT_PUBLIC_BASE_PATH || "";
      const res = await fetch(`${base}/api/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (res.ok) {
        setStatus("sent");
        return;
      }
      setStatus("error");
      setMessage(res.status === 503 ? t.unavailable : res.status === 400 ? t.required : t.error);
    } catch {
      setStatus("error");
      setMessage(t.error);
    }
  }

  if (status === "sent") {
    return (
      <div role="status" className={cn("rounded-theme-lg border-theme border-line bg-surface p-8", className)}>
        <p className="t-title text-ink">{t.success}</p>
      </div>
    );
  }

  const label = "t-label mb-2 block text-ink";
  return (
    <form onSubmit={onSubmit} noValidate className={cn("grid gap-5", className)}>
      {t.heading && <p className="t-title text-ink">{t.heading}</p>}
      <div>
        <label htmlFor={id("name")} className={label}>{t.labels.name}</label>
        <input id={id("name")} name="name" autoComplete="name" required className="field" />
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor={id("phone")} className={label}>{t.labels.phone}</label>
          <input id={id("phone")} name="phone" type="tel" autoComplete="tel" inputMode="tel" className="field" />
        </div>
        <div>
          <label htmlFor={id("email")} className={label}>
            {t.labels.email} <span className="font-normal normal-case tracking-normal text-muted">({t.optional})</span>
          </label>
          <input id={id("email")} name="email" type="email" autoComplete="email" className="field" />
        </div>
      </div>
      {t.services.length > 0 && (
        <div>
          <label htmlFor={id("service")} className={label}>{t.labels.service}</label>
          <div className="relative">
            <select id={id("service")} name="service" className="field appearance-none pr-11">
              {t.services.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
            <ChevronDown aria-hidden="true" className="pointer-events-none absolute right-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" />
          </div>
        </div>
      )}
      <div>
        <label htmlFor={id("message")} className={label}>{t.labels.message}</label>
        <textarea id={id("message")} name="message" rows={4} className="field min-h-[7.5rem] resize-y" />
      </div>
      {status === "error" && message && (
        <p role="alert" className="rounded-theme border-theme border-line bg-accent-soft px-4 py-3 text-ink">
          {message}
          {t.telHref && (
            <>
              {" "}
              <a href={t.telHref} className="link whitespace-nowrap">{t.phoneDisplay}</a>
            </>
          )}
        </p>
      )}
      <button type="submit" disabled={status === "sending"} className="btn btn-primary btn-lg w-full sm:w-auto sm:justify-self-start">
        {status === "sending" ? (
          <>
            <MorphingSquare className="h-4 w-4 bg-current" />
            <span>{t.sending}</span>
          </>
        ) : (
          t.submit
        )}
      </button>
    </form>
  );
}
