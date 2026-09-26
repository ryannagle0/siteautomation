import {
  ShieldCheckIcon,
  TagIcon,
  CertificateIcon,
  PlugIcon,
  PhoneIcon,
} from "./icons";

const ITEMS = [
  { icon: ShieldCheckIcon, label: "Safe Electric Registered" },
  { icon: TagIcon, label: "20+ Years Experience" },
  { icon: CertificateIcon, label: "Completion Certificate Every Job" },
  { icon: PlugIcon, label: "Solar & EV Charging" },
  { icon: PhoneIcon, label: "24/7 Emergency Callout" },
];

export function TrustBar() {
  return (
    <section data-slot="trust" className="bg-grey-section">
      <div className="mx-auto flex max-w-content flex-wrap items-center justify-center gap-x-10 gap-y-5 px-6 py-8 lg:flex-nowrap lg:justify-between lg:px-16">
        {ITEMS.map((item) => (
          <div key={item.label} className="flex items-center gap-2.5">
            <item.icon width={18} height={18} className="shrink-0 text-blue" />
            <span className="whitespace-nowrap text-[13px] font-medium text-navy/75">
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
