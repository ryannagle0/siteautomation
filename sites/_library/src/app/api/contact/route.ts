import { NextResponse } from "next/server";
import { Resend } from "resend";
import { biz } from "@/lib/content";

// Quote requests are emailed to the business with Resend. Without
// RESEND_API_KEY (or without a business email) the form tells the visitor
// to call instead of pretending the message was sent.
export async function POST(req: Request) {
  let body: Record<string, unknown> = {};
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Please fill in the form and try again." }, { status: 400 });
  }
  const field = (k: string) => (typeof body[k] === "string" ? (body[k] as string).trim().slice(0, 4000) : "");
  const name = field("name");
  const phone = field("phone");
  const email = field("email");
  const service = field("service");
  const message = field("message");

  if (!name || (!phone && !email)) {
    return NextResponse.json({ error: "Please add your name and a phone number or email." }, { status: 400 });
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey || !biz.email) {
    return NextResponse.json({ error: "unavailable" }, { status: 503 });
  }

  try {
    const resend = new Resend(apiKey);
    const { error } = await resend.emails.send({
      from: `${biz.name} Website <onboarding@resend.dev>`,
      to: biz.email,
      ...(email ? { replyTo: email } : {}),
      subject: `New enquiry${service ? ` — ${service}` : ""} from ${name}`,
      text: [`Name: ${name}`, `Phone: ${phone || "-"}`, `Email: ${email || "-"}`, `Service: ${service || "-"}`, "", message || "(no message)"].join("\n"),
    });
    if (error) return NextResponse.json({ error: "send-failed" }, { status: 502 });
    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "send-failed" }, { status: 502 });
  }
}
