# Virasat

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Buyers discover and purchase handmade Indian craft. Artisans describe and publish work, fulfil orders and answer custom requests. Verifiers review artisan profiles. Administrators maintain records through Django Admin. The project is also evaluated for the INT253 course.

## Product Purpose

Connect buyers to named makers and craft traditions, with clear product information, a working purchase flow and transparent artisan earnings.

## Positioning

The catalog combines regional craft context, artisan profiles, editable English and Hindi descriptions, and buyer briefs with artisan proposals. These are implemented flows, not promised future features.

## Operating Context

The site must work on phones, including users with limited digital literacy. Demo accounts and deterministic seed data support evaluation. The marketplace works without an AI key. Installation and a friendly offline page are optional PWA support, not offline shopping.

## Capabilities and Constraints

- Preserve function views, Django templates, forms, ORM, authentication, sessions, cookies and all existing permissions and URLs.
- Use HTML, CSS and Bootstrap 5.3. Custom application JavaScript remains restricted to the existing PWA scripts. No UI framework migration.
- Preserve models, migrations and POST behaviour. Small presentation context changes are allowed.
- Payments are demonstrations; no money moves. No delivery logistics or messaging system is claimed.
- Use original generated craft imagery or user-owned photos. Do not substitute downloaded stock photographs or invent maker portraits.
- U+2014 and U+2013 are forbidden in project content. AI and fallback text retain their cleaning guard.
- All existing tests must continue to pass. Maintain keyboard access, readable contrast, responsive layouts and Hindi support.

## Brand Commitments

The name is Virasat. The user wants simple, credible, visibly well-designed UI rather than an ornate AI-generated template. On 24 November 2026 the user explicitly approved replacing the previous fonts, color treatment and visual style. This permission does not remove the functional or technology constraints.

## Evidence on Hand

Actual product titles, prices, stock, craft traditions, maker profiles and marketplace figures come from the database. `catalog/art.py` generates deterministic original craft artwork. Existing test and screenshot evidence is in `docs/`. No real customer testimonials, guarantees, live payment service, repository URL or deployed domain may be invented.

## Product Principles

1. Show the work and its maker before decorative interface elements.
2. Make the next shopping or workshop action obvious.
3. Keep claims traceable to the implementation and data.
4. Prefer clarity and useful detail over animation and ornament.
5. Preserve the fully usable no-key flow.

## Accessibility and Inclusion

Phone layouts must not scroll horizontally. Use visible focus, labelled controls, readable input sizes, useful errors, Hindi text support and a skip link. Product cards remain two columns on mobile as originally requested.
