import { Img } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { content, hasImage } from "@/lib/content";

/**
 * Photo one side, story the other. Without a photo the heading takes the
 * left column at headline scale and the story reads beside it.
 */
export default function AboutSplit({ tone = "surface" }: { tone?: Tone }) {
  const about = content.about;
  if (!about?.heading) return null;
  const img = hasImage(about.image) ? about.image : null;
  return (
    <Section slot="about" id="about" tone={tone}>
      <div className="wrap section-y grid gap-10 md:grid-cols-12 md:items-center md:gap-14">
        {img ? (
          <>
            <Img img={img} ratio="4 / 3" className="md:col-span-5 md:!aspect-[4/5]" sizes="(min-width: 768px) 40vw, 100vw" />
            <div className="md:col-span-7 lg:pl-6">
              <T k="about.heading" as="h2" className="t-headline text-ink" />
              <Body />
            </div>
          </>
        ) : (
          <>
            <T k="about.heading" as="h2" className="t-headline text-ink md:col-span-5 md:self-start" />
            <div className="md:col-span-7">
              <Body first />
            </div>
          </>
        )}
      </div>
    </Section>
  );
}

function Body({ first = false }: { first?: boolean }) {
  const body = (content.about?.body || []).filter(Boolean);
  return (
    <div className={`t-body ${first ? "" : "mt-6"}`}>
      {body.map((_, i) => (
        <T key={i} k={`about.body.${i}`} as="p" className={i === 0 ? "t-lead !text-ink" : "text-muted"} />
      ))}
    </div>
  );
}
