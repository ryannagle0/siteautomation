import type { SVGProps } from "react";

function base(props: SVGProps<SVGSVGElement>) {
  return {
    width: 22,
    height: 22,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.6,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    ...props,
  };
}

export function BoltIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8Z" />
    </svg>
  );
}

export function PhoneIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M4 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L14 13l5 2v4a2 2 0 0 1-2 2C9.5 21 3 14.5 3 6a2 2 0 0 1 2-2Z" />
    </svg>
  );
}

export function WhatsAppIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M7 17.5 4 20l1.4-3.9A8 8 0 1 1 12 20a8 8 0 0 1-5-1.5Z" />
      <path d="M9 9c0 3 2.2 6 6 6" strokeDasharray="0.1 3" />
      <path d="M9 9.3c.2-1 1.6-.9 1.8-.1.2.7-.4 1.3-.1 2 .5 1.2 1.8 2.5 3 3 .7.3 1.3-.3 2-.1.8.2.9 1.6-.1 1.8-3 .6-6.1-2.5-6.6-6.6Z" />
    </svg>
  );
}

export function MailIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <rect x="3" y="5" width="18" height="14" rx="1" />
      <path d="m4 6 8 7 8-7" />
    </svg>
  );
}

export function PinIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 22s7-7.5 7-12.5A7 7 0 0 0 5 9.5C5 14.5 12 22 12 22Z" />
      <circle cx="12" cy="9.5" r="2.3" />
    </svg>
  );
}

export function ShieldCheckIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6l-7-3Z" />
      <path d="m9 12 2 2 4-4.5" />
    </svg>
  );
}

export function UmbrellaIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 3C7 3 3 7 3 11h18c0-4-4-8-9-8Z" />
      <path d="M12 11v8a2 2 0 0 1-4 0" />
      <path d="M12 3v1" />
    </svg>
  );
}

export function TagIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 3h6a2 2 0 0 1 2 2v6l-9 9-8-8 9-9Z" />
      <circle cx="15.5" cy="7.5" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function CalendarIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <rect x="3" y="5" width="18" height="16" rx="1" />
      <path d="M3 9h18M8 3v4M16 3v4" />
    </svg>
  );
}

export function CertificateIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <rect x="3" y="4" width="18" height="12" rx="1" />
      <path d="m8 20 4-2 4 2v-4H8Z" />
      <path d="M7 8h10M7 11h6" />
    </svg>
  );
}

export function HouseIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M4 11 12 4l8 7" />
      <path d="M6 9.5V20h12V9.5" />
      <path d="M10 20v-6h4v6" />
    </svg>
  );
}

export function PlugIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M9 2v6M15 2v6M7 8h10v4a5 5 0 0 1-10 0V8Z" />
      <path d="M12 17v5" />
    </svg>
  );
}

export function BuildingIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <rect x="4" y="3" width="16" height="18" rx="1" />
      <path d="M8 7h1M8 11h1M8 15h1M15 7h1M15 11h1M15 15h1" />
      <path d="M10 21v-4h4v4" />
    </svg>
  );
}

export function FlameIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 2c1 3-3 4-3 7a3 3 0 0 0 6 0c1.5 1.5 2 3.5 2 5a5 5 0 1 1-10 0c0-4 3-6 3-8 0-1.5 1-3 2-4Z" />
    </svg>
  );
}

export function LampIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 2v3M5 9l2 2M19 9l-2 2" />
      <circle cx="12" cy="12" r="4" />
      <path d="M9 20h6M12 16v4" />
    </svg>
  );
}

export function AlertIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M12 3 2 20h20L12 3Z" />
      <path d="M12 10v4M12 17h.01" />
    </svg>
  );
}

export function CheckIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M4 12.5 9.5 18 20 6" />
    </svg>
  );
}

export function StarIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width={16}
      height={16}
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="none"
      {...props}
    >
      <path d="M12 2.5 15 9l7 .9-5.2 5 1.3 7-6.1-3.4L5.9 22l1.3-7L2 9.9 9 9l3-6.5Z" />
    </svg>
  );
}

export function MenuIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  );
}

export function CloseIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M5 5l14 14M19 5 5 19" />
    </svg>
  );
}

export function ArrowRightIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg {...base(props)}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}
