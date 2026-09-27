# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

One person: the owner, a solo operator who sells websites to Irish tradespeople. They use the SiteForge dashboard to find leads, generate and polish a demo site for each business, and send it to the owner as the pitch.

The second audience is each tradesperson who receives a demo, such as an electrician, plumber, roofer or landscaper. They are usually on a phone, judging in seconds whether the site looks like their business and looks better than what they have now: no site, a free-builder site, or a Facebook page.

## Product Purpose

SiteForge turns a Google Maps listing into a finished, personalised demo website fast enough to send one to every promising lead. It follows the whole loop:
- Search Places by trade and county.
- Score each lead and enrich it with email, logo and brand colours.
- Build a Next.js site from the master template.
- Edit with AI, themes, components, logos and inline text.
- Deploy to Vercel.
- Email the owner.

Success means a tradesperson opens their demo and signs up for a monthly subscription.

## Positioning

A generic site builder or agency template can't copy two things:
- **Personalisation:** each demo already *is* the prospect's business before they've been contacted. It has their name, town, phone, their own logo emblem, their colours and real reviews context.
- **Speed:** one operator can produce demos at lead volume, not one per day.

## Operating Context

- **Where the operator works:** in the dashboard, locally on Windows or hosted on Railway. Leads flow Leads → Pipeline → Edit Site → Deploy → Emails.
- **Demo sites:** built per lead in `sites/<slug>` from the master template `sites/derek-doyle-electrical`. They are previewed live, edited, and deployed to `<slug>.vercel.app`.
- **Outreach:** email first; the demo link is the pitch.

## Capabilities and Constraints

- **Stack:**
  - Flask + vanilla JS dashboard, in `templates/index.html` and `app.py`.
  - Demo sites are Next.js + Tailwind + framer-motion.
  - Logo processing is in `logos.py`.
  - Claude Haiku handles edits and vision.
  - 21st.dev MCP supplies components.
  - Google Places (New) provides leads; the Enterprise-tier fields cost money beyond the free quota.
- **Market:** Ireland only, trades only; electricians first, since the template is electrician-flavoured.
- **Business model:** a monthly subscription covering the site, hosting and edits. Price not recorded.
- **Dashboard rules:** keep the existing dark dashboard styling, and don't break existing features.
- **Hosted limits:** on Railway, previews are proxied without hot reload, and each running preview costs memory.

## Brand Commitments

- **SiteForge:** an internal tool with its own dark dashboard. It isn't customer-facing.
- **Demo sites:** carry the *prospect's* brand, never SiteForge's. Their logo appears only as its emblem, never as the full logo with baked-in text beside the business name. Their brand colours drive the accent.

## Evidence on Hand

- **Per-lead real data:** Google rating and review count, Maps link, website, extracted emblems and brand colours.
- **Template facts:** the master template states Safe Electric registration, 20+ years and RECI membership. These are true only for the original business, so they must be verified per lead, not assumed.
- **What doesn't exist:** customer testimonials about SiteForge, conversion statistics, or published pricing. Don't fabricate them, and don't invent reviews or credentials on demo sites.

## Product Principles

1. **It must look like their business.** Personalisation from real data beats any generic polish.
2. **Premium and trustworthy.** Every demo should be clearly better than the prospect's current presence, at a glance on a phone.
3. **Operator speed.** Every workflow is judged by minutes per lead and manual steps saved.
4. **Never fabricate.** Only real facts about the prospect: no invented reviews, credentials, years or claims.
5. **Safe edits.** Every change is snapshotted and undoable; don't break existing features.
