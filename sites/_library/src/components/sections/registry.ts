import type { ComponentType } from "react";
import type { Tone } from "@/components/Section";
import NavCentredLogo from "./nav/nav-centred-logo";
import NavMinimal from "./nav/nav-minimal";
import NavPhoneBar from "./nav/nav-phone-bar";
import HeroFullBleed from "./hero/hero-full-bleed";
import HeroImageGrid from "./hero/hero-image-grid";
import HeroReviewLed from "./hero/hero-review-led";
import HeroSplitImage from "./hero/hero-split-image";
import HeroTypographic from "./hero/hero-typographic";
import TrustGrid from "./trust/trust-grid";
import TrustRating from "./trust/trust-rating";
import TrustStrip from "./trust/trust-strip";
import ServicesFeaturedGrid from "./services/services-featured-grid";
import ServicesGrid from "./services/services-grid";
import ServicesListIcons from "./services/services-list-icons";
import ServicesTabs from "./services/services-tabs";
import AboutFacts from "./about/about-facts";
import AboutOwnerNote from "./about/about-owner-note";
import AboutSplit from "./about/about-split";
import ProcessCards from "./process/process-cards";
import ProcessSteps from "./process/process-steps";
import ProcessTimeline from "./process/process-timeline";
import ReviewsCarousel from "./reviews/reviews-carousel";
import ReviewsFeatured from "./reviews/reviews-featured";
import ReviewsGrid from "./reviews/reviews-grid";
import GalleryGrid from "./gallery/gallery-grid";
import GalleryMosaic from "./gallery/gallery-mosaic";
import AreaMap from "./service-area/area-map";
import AreaTowns from "./service-area/area-towns";
import CtaBand from "./cta/cta-band";
import CtaCallout from "./cta/cta-callout";
import CtaSplit from "./cta/cta-split";
import ContactDetails from "./contact/contact-details";
import ContactFormCentered from "./contact/contact-form-centered";
import ContactFormSplit from "./contact/contact-form-split";
import FooterBigPhone from "./footer/footer-big-phone";
import FooterColumns from "./footer/footer-columns";
import FooterSimple from "./footer/footer-simple";

export type SectionEntry = { slot: string; variant: string; tone?: Tone };
export type SectionProps = { tone?: Tone };

/**
 * Every section variant, by id. sections.json refers to these ids; the
 * catalogue (sites/_library/catalogue.json) describes each one for the AI
 * that composes a site. Add a variant: create the file, register it here,
 * describe it in catalogue.json.
 */
export const SECTIONS: Record<string, ComponentType<SectionProps>> = {
  "nav-centred-logo": NavCentredLogo,
  "nav-minimal": NavMinimal,
  "nav-phone-bar": NavPhoneBar,
  "hero-full-bleed": HeroFullBleed,
  "hero-image-grid": HeroImageGrid,
  "hero-review-led": HeroReviewLed,
  "hero-split-image": HeroSplitImage,
  "hero-typographic": HeroTypographic,
  "trust-grid": TrustGrid,
  "trust-rating": TrustRating,
  "trust-strip": TrustStrip,
  "services-featured-grid": ServicesFeaturedGrid,
  "services-grid": ServicesGrid,
  "services-list-icons": ServicesListIcons,
  "services-tabs": ServicesTabs,
  "about-facts": AboutFacts,
  "about-owner-note": AboutOwnerNote,
  "about-split": AboutSplit,
  "process-cards": ProcessCards,
  "process-steps": ProcessSteps,
  "process-timeline": ProcessTimeline,
  "reviews-carousel": ReviewsCarousel,
  "reviews-featured": ReviewsFeatured,
  "reviews-grid": ReviewsGrid,
  "gallery-grid": GalleryGrid,
  "gallery-mosaic": GalleryMosaic,
  "area-map": AreaMap,
  "area-towns": AreaTowns,
  "cta-band": CtaBand,
  "cta-callout": CtaCallout,
  "cta-split": CtaSplit,
  "contact-details": ContactDetails,
  "contact-form-centered": ContactFormCentered,
  "contact-form-split": ContactFormSplit,
  "footer-big-phone": FooterBigPhone,
  "footer-columns": FooterColumns,
  "footer-simple": FooterSimple,
};
