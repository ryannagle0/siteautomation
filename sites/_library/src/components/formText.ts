import type { FormText } from "@/components/ContactForm";
import { content, phone, telHref, ui } from "@/lib/content";

/** Everything the (client) form needs to say, read from content.json on the server. */
export function formText(withHeading = false): FormText {
  const c = content.contact;
  const l = c?.labels || {};
  return {
    heading: withHeading ? c?.formHeading : undefined,
    submit: c?.submit || ui("quote"),
    success: c?.success || "",
    sending: ui("sending"),
    required: ui("formRequired"),
    unavailable: ui("formUnavailable"),
    error: ui("formError"),
    optional: ui("optional"),
    labels: {
      name: l.name || ui("name"),
      phone: l.phone || ui("phone"),
      email: l.email || ui("email"),
      service: l.service || ui("service"),
      message: l.message || ui("message"),
    },
    services: (c?.services || []).filter(Boolean),
    telHref,
    phoneDisplay: phone?.display || "",
  };
}
