# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

People in a town in Ireland who need a tradesperson or a local business: homeowners with a tripped board, a leaking tank or a garden gone wild, small offices needing a fit-out, someone looking for a café near the office. They are almost always on a phone, often mid-problem, comparing two or three local names in a few seconds each. The job: decide who looks real, local and trustworthy enough to ring.

The second reader is the business owner themselves (an electrician, plumber, roofer, landscaper, builder or café owner) opening a SiteForge demo of *their* site for the first time. They judge in seconds whether it looks like their business and looks better than what they have now.

## Product Purpose

The section library is what SiteForge composes each demo site from. Every page has one goal: a phone call, a WhatsApp message or a quote request. Success means a visitor on a phone can see who this is, where they work and how to contact them within the first screen, and can do it with one thumb from anywhere on the page.

## Positioning

The site already *is* the business: their name, town, phone, emblem, brand colour, real Google rating and real review text, on a page built for how local people actually choose a tradesperson. A national directory listing or a template builder page can't be that specific.

## Operating Context

- **Composition:** SiteForge picks one of four style presets and one variant per slot (nav, hero, trust, services, about, process, reviews, gallery, service-area, CTA, contact, footer). `catalogue.json` describes every variant.
- **Data:** each site is built at speed from thin, real data: business name, trade, town, county, phone, sometimes an email, sometimes a Google rating with review text, a brand colour from their logo, and at most a few photos (Gemini-generated scene photos that passed a quality check, or none).
- **Editing:** the operator edits copy inline (every text node maps to a key in `content.json`), asks Claude for changes, swaps sections for 21st.dev components, and changes accent colour or preset from the dashboard.

## Capabilities and Constraints

- **Stack:** Next.js 14 App Router, TypeScript and Tailwind. All copy lives in `src/content.json`, section order and variants in `src/sections.json`, design tokens in `src/tokens.css`.
- **Missing data is normal:** no photos, no email, no reviews, very long or very short business names. Every variant must still look finished.
- **Phones first:** 390px is the primary viewport. A sticky Call / WhatsApp bar is always present on mobile.
- **Hosting:** Vercel. The same code also runs under a `/preview/<slug>` base path in SiteForge's hosted preview.

## Brand Commitments

- **Visible brand:** each site carries the prospect's brand, never SiteForge's.
- **Accent:** comes from the business's own brand colour at build time.
- **Tone:** trustworthy, local, established, premium but not corporate.
- **Anti-references:**
  - generic Wix / FCR Media templates
  - stock-photo clutter
  - SaaS landing pages
  - purple gradients
  - fake urgency ("only 2 slots left!")

## Evidence on Hand

- **Real per-lead data:** name, phone, town, county, trade, Google rating and review count, and up to five real Google reviews (author, stars, text).
- **Unverified facts:** registrations (Safe Electric, RGII, RECI), insurance, years in business, awards and prices are never known. Don't state them unless the operator adds them.
- **Photos:** AI-generated photos show the trade, not the business's own jobs. Never caption them as "our work". A gallery only renders with real photos.

## Product Principles

1. **One thumb to the phone.** The call is never more than one tap away, on every screen size.
2. **Local before generic.** Town names, the county, the owner's first name and real reviews do more than any adjective.
3. **Finished with nothing.** A site with no photos, no email and no reviews must still look deliberate, never half-empty.
4. **Never fabricate.** No invented reviews, credentials, years, prices or claims.
5. **Editable by design.** Every visible word is a key in `content.json`. Every section is one file the operator can swap.

## Accessibility & Inclusion

- **Standard:** WCAG 2.2 AA.
- **Contrast:** at least 4.5:1 for body text, including accent text computed against each preset's background.
- **Tap targets:** at least 44px.
- **Motion:** honour reduced motion.
- **Readers:** many visitors are older homeowners, so body text starts at 17px.
