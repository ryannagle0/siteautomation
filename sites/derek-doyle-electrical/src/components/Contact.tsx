"use client";

import { useState, type FormEvent } from "react";
import { FadeUp } from "./motion/FadeUp";
import { PhoneIcon, WhatsAppIcon, MailIcon, PinIcon, CheckIcon } from "./icons";
import { MorphingSquare } from "./ui/morphing-square";
import {
  Map,
  MapMarker,
  MarkerContent,
  MarkerLabel,
  MarkerTooltip,
} from "./ui/mapcn-marker-label";

const OFFICE_LOCATION = { longitude: {{LNG}}, latitude: {{LAT}} };

const SERVICES = [
  "Domestic Rewires",
  "EV Charger Installation",
  "Commercial Electrical",
  "Fire Alarm Systems",
  "Festive Lighting",
  "Emergency Callout",
  "Other",
];

const CONTACT_ITEMS = [
  { icon: PhoneIcon, label: "Phone", value: "{{PHONE_DISPLAY}}", href: "tel:{{PHONE_TEL}}" },
  {
    icon: WhatsAppIcon,
    label: "WhatsApp",
    value: "{{PHONE_DISPLAY}}",
    href: "https://wa.me/{{PHONE_WA}}",
  },
  {
    icon: MailIcon,
    label: "Email",
    value: "{{EMAIL}}",
    href: "mailto:{{EMAIL}}",
  },
  {
    icon: PinIcon,
    label: "Location",
    value: "{{TOWN}} coverage",
    href: undefined,
  },
];

type Status = "idle" | "submitting" | "success" | "error";

export function Contact() {
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("submitting");
    setErrorMsg("");

    const form = e.currentTarget;
    const data = new FormData(form);
    const payload = {
      name: data.get("name"),
      phone: data.get("phone"),
      email: data.get("email"),
      service: data.get("service"),
      message: data.get("message"),
    };

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const json = await res.json().catch(() => null);
        throw new Error(json?.error || "Something went wrong.");
      }
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <section id="contact" className="bg-navy px-6 py-24 lg:px-16 lg:py-36">
      <div className="mx-auto max-w-content">
        <div className="grid grid-cols-1 items-stretch gap-12 lg:grid-cols-2">
        <FadeUp>
          <p className="text-[13px] font-semibold uppercase tracking-wide text-blue">
            Get In Touch
          </p>
          <h2 className="mt-4 text-balance text-4xl font-semibold tracking-tightest text-white sm:text-[2.75rem]">
            Get a free quote.
          </h2>
          <p className="mt-6 max-w-md text-[15.5px] leading-relaxed text-white/55">
            We cover all of {{TOWN}}. Call, WhatsApp or fill in
            the form and we&rsquo;ll get back to you the same day.
          </p>

          <div className="mt-10 flex flex-col gap-5">
            {CONTACT_ITEMS.map((item) => {
              const inner = (
                <>
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-sharp bg-white/5 text-blue transition-colors group-hover:bg-blue group-hover:text-white">
                    <item.icon width={19} height={19} />
                  </span>
                  <span>
                    <span className="block text-[11.5px] font-medium uppercase tracking-wide text-white/40">
                      {item.label}
                    </span>
                    <span className="block text-[15px] font-medium text-white">
                      {item.value}
                    </span>
                  </span>
                </>
              );
              return item.href ? (
                <a key={item.label} href={item.href} className="group flex items-center gap-4">
                  {inner}
                </a>
              ) : (
                <div key={item.label} className="group flex items-center gap-4">
                  {inner}
                </div>
              );
            })}
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <div className="h-full rounded-sharp bg-white p-7 sm:p-9">
            {status === "success" ? (
              <div className="flex min-h-[380px] flex-col items-center justify-center text-center">
                <span className="flex h-14 w-14 items-center justify-center rounded-sharp bg-blue/10 text-blue">
                  <CheckIcon width={26} height={26} strokeWidth={2.2} />
                </span>
                <h3 className="mt-6 text-xl font-semibold text-navy">
                  Message sent.
                </h3>
                <p className="mt-2 max-w-xs text-[14.5px] text-navy/60">
                  Thanks — we&rsquo;ve got your request and will get back to you
                  the same day.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                <div>
                  <label htmlFor="name" className="mb-1.5 block text-[12.5px] font-medium text-navy/70">
                    Full name
                  </label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    className="w-full rounded-sharp border border-grey-line px-4 py-3 text-[15px] text-navy outline-none transition-colors focus:border-blue"
                  />
                </div>
                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                  <div>
                    <label htmlFor="phone" className="mb-1.5 block text-[12.5px] font-medium text-navy/70">
                      Phone number
                    </label>
                    <input
                      id="phone"
                      name="phone"
                      type="tel"
                      required
                      className="w-full rounded-sharp border border-grey-line px-4 py-3 text-[15px] text-navy outline-none transition-colors focus:border-blue"
                    />
                  </div>
                  <div>
                    <label htmlFor="email" className="mb-1.5 block text-[12.5px] font-medium text-navy/70">
                      Email
                    </label>
                    <input
                      id="email"
                      name="email"
                      type="email"
                      required
                      className="w-full rounded-sharp border border-grey-line px-4 py-3 text-[15px] text-navy outline-none transition-colors focus:border-blue"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="service" className="mb-1.5 block text-[12.5px] font-medium text-navy/70">
                    Service needed
                  </label>
                  <select
                    id="service"
                    name="service"
                    required
                    defaultValue=""
                    className="w-full rounded-sharp border border-grey-line px-4 py-3 text-[15px] text-navy outline-none transition-colors focus:border-blue"
                  >
                    <option value="" disabled>
                      Select a service
                    </option>
                    {SERVICES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="message" className="mb-1.5 block text-[12.5px] font-medium text-navy/70">
                    Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    rows={4}
                    className="w-full resize-none rounded-sharp border border-grey-line px-4 py-3 text-[15px] text-navy outline-none transition-colors focus:border-blue"
                  />
                </div>

                {status === "error" && (
                  <p className="text-sm text-red-600">{errorMsg}</p>
                )}

                <button
                  type="submit"
                  disabled={status === "submitting"}
                  className="mt-1 flex items-center justify-center rounded-sharp bg-blue px-7 py-4 text-[15px] font-semibold text-white transition-colors hover:bg-blue-dark disabled:opacity-60"
                >
                  {status === "submitting" ? (
                    <MorphingSquare className="h-4 w-4 bg-white" />
                  ) : (
                    "Send message"
                  )}
                </button>
              </form>
            )}
          </div>
        </FadeUp>
        </div>

        <div
          className="mt-24 w-full overflow-hidden rounded-lg"
          style={{
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: "8px",
            height: "350px",
          }}
        >
          <Map
            center={[OFFICE_LOCATION.longitude, OFFICE_LOCATION.latitude]}
            zoom={13}
            theme="light"
            styles={{
              light: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            }}
          >
            <MapMarker
              longitude={OFFICE_LOCATION.longitude}
              latitude={OFFICE_LOCATION.latitude}
            >
              <MarkerContent>
                <div
                  className="rounded-full"
                  style={{
                    width: 16,
                    height: 16,
                    backgroundColor: "#1D4ED8",
                    border: "2px solid white",
                  }}
                />
                <MarkerLabel
                  position="bottom"
                  className="!text-[11px] !font-semibold !text-[#111111]"
                >
                  {{BUSINESS_NAME}}
                </MarkerLabel>
              </MarkerContent>
              <MarkerTooltip>{{PHONE_DISPLAY}}</MarkerTooltip>
            </MapMarker>
          </Map>
        </div>
      </div>
    </section>
  );
}
