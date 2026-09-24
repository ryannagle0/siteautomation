import { NextResponse } from "next/server";
import { Resend } from "resend";

const TO_EMAIL = "{{EMAIL}}";

export async function POST(req: Request) {
  const body = await req.json();
  const { name, phone, email, service, message } = body ?? {};

  if (!name || !phone || !email || !service) {
    return NextResponse.json(
      { error: "Please fill in all required fields." },
      { status: 400 }
    );
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "Email service is not configured." },
      { status: 500 }
    );
  }

  try {
    const resend = new Resend(apiKey);
    const { error } = await resend.emails.send({
      from: "{{BUSINESS_NAME}} Website <onboarding@resend.dev>",
      to: TO_EMAIL,
      replyTo: email,
      subject: `New quote request — ${service}`,
      text: [
        `Name: ${name}`,
        `Phone: ${phone}`,
        `Email: ${email}`,
        `Service needed: ${service}`,
        "",
        "Message:",
        message || "(none provided)",
      ].join("\n"),
    });

    if (error) {
      return NextResponse.json({ error: "Failed to send message." }, { status: 502 });
    }

    return NextResponse.json({ ok: true });
  } catch {
    return NextResponse.json({ error: "Failed to send message." }, { status: 500 });
  }
}
