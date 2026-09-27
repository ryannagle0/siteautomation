import { BrandMark } from "@/components/BrandMark";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PhoneBig } from "@/components/parts";
import { biz, mailHref, ui } from "@/lib/content";

/** The number as the last thing on the page, at poster size. */
export default function FooterBigPhone({ tone = "band" }: { tone?: Tone }) {
  return (
    <Section slot="footer" as="footer" tone={tone}>
      <div className="wrap pb-10 pt-16 md:pt-24">
        <PhoneBig className="[&>span:last-child]:text-[clamp(2.6rem,9vw,7.5rem)]" />
        <div className="mt-12 flex flex-col gap-6 border-t border-line pt-8 md:flex-row md:items-end md:justify-between">
          <div>
            <BrandMark nameClassName="text-lg leading-tight" />
            <T k="footer.blurb" as="p" className="mt-2 max-w-md text-step-small text-muted" />
          </div>
          <div className="flex flex-col gap-2 text-step-small md:items-end">
            {biz.email && (
              <a href={mailHref} data-edit="business.email" className="text-ink no-underline hover:text-accent-ink">{biz.email}</a>
            )}
            <a href="#top" className="text-muted no-underline hover:text-ink">{ui("backToTop")}</a>
            <T k="footer.legal" as="p" className="text-step--2 text-muted" />
          </div>
        </div>
      </div>
    </Section>
  );
}
