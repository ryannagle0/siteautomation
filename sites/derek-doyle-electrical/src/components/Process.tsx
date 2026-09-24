import { FadeUp, StaggerGrid, StaggerItem } from "./motion/FadeUp";
import { PhoneIcon, CalendarIcon, CertificateIcon } from "./icons";

const STEPS = [
  {
    num: "1",
    icon: PhoneIcon,
    title: "Call or WhatsApp {{OWNER_FIRST_NAME}}",
    desc: "Available 24/7 for emergencies across {{TOWN}}.",
  },
  {
    num: "2",
    icon: CalendarIcon,
    title: "Free site visit & quote",
    desc: "We come out, look at the job properly and give you a clear written price. No call-out charge.",
  },
  {
    num: "3",
    icon: CertificateIcon,
    title: "Work done & certified",
    desc: "Completed to Safe Electric standard, tested, signed off. Certificate handed to you on the day.",
  },
];

export function Process() {
  return (
    <section id="process" className="bg-base px-6 py-24 lg:px-16 lg:py-36">
      <div className="mx-auto max-w-content">
        <FadeUp className="max-w-xl">
          <p className="text-[13px] font-semibold uppercase tracking-wide text-blue">
            The Process
          </p>
          <h2 className="mt-4 text-balance text-4xl font-semibold tracking-tightest text-navy sm:text-[2.75rem]">
            Simple from first call to final cert.
          </h2>
        </FadeUp>

        <StaggerGrid className="mt-14 grid grid-cols-1 gap-8 lg:grid-cols-3 lg:gap-6">
          {STEPS.map((s) => (
            <StaggerItem key={s.num}>
              <div className="relative overflow-hidden rounded-sharp border border-grey-line p-8">
                <span
                  aria-hidden
                  className="num-tabular pointer-events-none absolute -right-2 -top-6 text-[7rem] font-bold leading-none text-navy/[0.05]"
                >
                  {s.num}
                </span>
                <span className="relative flex h-11 w-11 items-center justify-center rounded-sharp bg-blue/10 text-blue">
                  <s.icon width={20} height={20} />
                </span>
                <h3 className="relative mt-6 text-lg font-semibold text-navy">
                  {s.title}
                </h3>
                <p className="relative mt-2.5 text-[14.5px] leading-relaxed text-navy/60">
                  {s.desc}
                </p>
              </div>
            </StaggerItem>
          ))}
        </StaggerGrid>
      </div>
    </section>
  );
}
