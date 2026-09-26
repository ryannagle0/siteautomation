import Image from "next/image";

const LINKS = [
  { href: "#services", label: "Services" },
  { href: "#about", label: "About" },
  { href: "#process", label: "Process" },
  { href: "#reviews", label: "Reviews" },
  { href: "#contact", label: "Contact" },
];

export function Footer() {
  return (
    <footer data-slot="footer" className="bg-ink px-6 py-10 lg:px-16">
      <div className="mx-auto flex max-w-content flex-col items-center gap-8 text-center lg:flex-row lg:justify-between lg:text-left">
        <div className="flex items-center gap-2.5">
          <Image
            src="/logo.png"
            alt="{{BUSINESS_NAME}}"
            width={24}
            height={24}
            className="object-contain"
          />
          <div>
            <p className="text-[13.5px] font-semibold text-white">
              {{BUSINESS_NAME}}
            </p>
            <p className="text-[11.5px] text-white/40">
              20 years experience. Zero shortcuts.
            </p>
          </div>
        </div>

        <nav className="flex flex-wrap items-center justify-center gap-x-7 gap-y-2">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-[13px] text-white/50 transition-colors hover:text-white"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <p className="text-[12px] text-white/35">
          Safe Electric Registered · Fully Insured · RECI Member · {{TOWN}} ·
          {{TOWN}} · © 2026 {{BUSINESS_NAME}}
        </p>
      </div>
    </footer>
  );
}
