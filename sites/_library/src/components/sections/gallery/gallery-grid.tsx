import { Img } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { Heading } from "@/components/parts";
import { content, hasImage } from "@/lib/content";

/** Even grid of real job photos with captions. Renders only with three or more photos. */
export default function GalleryGrid({ tone = "base" }: { tone?: Tone }) {
  const images = (content.gallery?.images || []).filter(hasImage).slice(0, 9);
  if (images.length < 3) return null;
  return (
    <Section slot="gallery" id="gallery" tone={tone}>
      <div className="wrap section-y">
        <Heading k="gallery.heading" intro="gallery.intro" />
        <ul className={`mt-12 grid gap-4 sm:grid-cols-2 lg:gap-6 ${images.length === 4 ? "" : "lg:grid-cols-3"}`}>
          {images.map((img, i) => (
            <li key={i}>
              <figure>
                <Img img={img} ratio="4 / 3" sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw" />
                {img.caption && (
                  <figcaption data-edit={`gallery.images.${i}.caption`} className="mt-3 text-step-small text-muted">{img.caption}</figcaption>
                )}
              </figure>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
