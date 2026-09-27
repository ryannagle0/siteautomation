import { Img } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { content, hasImage } from "@/lib/content";

/** A short letter from the owner, signed. Works best when there's a real first name. */
export default function AboutOwnerNote({ tone = "base" }: { tone?: Tone }) {
  const about = content.about;
  if (!about?.heading) return null;
  const body = (about.body || []).filter(Boolean);
  const img = hasImage(about.image) ? about.image : null;
  return (
    <Section slot="about" id="about" tone={tone}>
      <div className="wrap section-y">
        <div className="grid gap-10 md:grid-cols-12 md:gap-14">
          <div className="md:col-span-8">
            <T k="about.heading" as="h2" className="t-headline text-ink" />
            <div className="t-body mt-8 text-step-1 leading-relaxed text-ink">
              {body.map((_, i) => (
                <T key={i} k={`about.body.${i}`} as="p" />
              ))}
            </div>
            {about.signoff && (
              <p className="mt-10 flex items-center gap-4">
                <span aria-hidden="true" className="h-px w-10 bg-accent" />
                <T k="about.signoff" className="text-step-1 font-semibold text-ink" />
              </p>
            )}
          </div>
          {img && (
            <div className="md:col-span-4">
              <Img img={img} ratio="3 / 4" sizes="(min-width: 768px) 30vw, 100vw" />
            </div>
          )}
        </div>
      </div>
    </Section>
  );
}
