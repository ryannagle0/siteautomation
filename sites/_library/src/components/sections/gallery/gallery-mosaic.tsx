import { Img } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { Heading } from "@/components/parts";
import { content, hasImage } from "@/lib/content";

/** One large photo leading a mosaic of smaller ones. Renders only with three or more photos. */
export default function GalleryMosaic({ tone = "surface" }: { tone?: Tone }) {
  const images = (content.gallery?.images || []).filter(hasImage).slice(0, 5);
  if (images.length < 3) return null;
  const [first, ...rest] = images;
  return (
    <Section slot="gallery" id="gallery" tone={tone}>
      <div className="wrap section-y">
        <Heading k="gallery.heading" intro="gallery.intro" />
        <div className="mt-12 grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
          <Img img={first} ratio="1 / 1" className="col-span-2 md:row-span-2 md:h-full" sizes="(min-width: 768px) 50vw, 100vw" />
          {rest.map((img, i) => (
            <Img key={i} img={img} ratio="1 / 1" sizes="(min-width: 768px) 25vw, 50vw" />
          ))}
        </div>
      </div>
    </Section>
  );
}
