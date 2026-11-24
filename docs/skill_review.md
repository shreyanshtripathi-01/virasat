# Taste Skill and Impeccable review: Selvedge

This is the final design review for the approved Selvedge storefront. It replaces the earlier review of the warm cream and serif direction, which is no longer the visual authority.

## Installation and scope

- Taste Skill 2.5.1 from `Leonxlnx/taste-skill`, installed as `design-taste-frontend` in `~/.agents/skills/`.
- Impeccable 4.10.0 from `pbakaus/impeccable`, installed in `~/.config/opencode/skills/`.
- `figma-designer` and `landing-page-design` from `elayadesign/ai-design-skills`, installed in `~/.agents/skills/`.
- All skill code stays outside the repository. No hooks were installed, and no application dependency, model, route, permission or custom JavaScript was added.
- The skills were loaded and used against the running Django application at desktop and phone sizes.

## Context and decisions

Kind: handmade marketplace with a storefront, buyer flows, artisan workspace and staff verification. The public surface persuades and the signed-in surface operates.

The user approved the Selvedge direction after an earlier review and gave explicit permission to replace the previous fonts, colours and styling. The current authority is `DESIGN.md`; product truth remains in `PRODUCT.md`. The old Playfair Display, Poppins, terracotta, indigo and turmeric system is history, not a requirement.

The project constraints still win over generic skill advice:

- Function-based views, Django templates, forms, ORM, sessions, cookies and auth only.
- No custom JavaScript outside PWA registration and the service worker.
- No new third-party Django packages.
- No AI key may be required for the storefront to work.
- No invented makers, reviews, guarantees, delivery integrations or payment claims.

## The Selvedge system

Selvedge is forest ink on a linen ground, with sage fields behind real craft work. Manrope carries display, body and labels, with Noto Sans Devanagari for Hindi. Product art supplies the colour; interface surfaces stay quiet.

The header is now the clearest signature of the system. A sticky linen bar closes with a dashed seam. The wordmark sits beside a circular maker seal with a forest V, a dotted stitch ring and a small sage dot. On hover or keyboard focus the stitch ring turns sixty degrees and the dot deepens to forest. Navigation lives in a white pill capsule; the current page becomes a solid forest pill through `aria-current="page"`. Cart, account and menu controls use matching pills, and the header call to action is the one solid forest pill in the bar.

The home page uses a split first viewport: copy, a working search and real marketplace figures on linen, then a large craft piece on sage with a white product label. Lower sections are editorial craft cards, a flat product grid, a maker directory, a forest request band and a sage statistics band. The system is documented in `DESIGN.md`.

## Review results

These are qualitative review scores, not a WCAG certificate or a measured performance benchmark.

| Dimension | Score | Evidence and limitation |
| --- | --- | --- |
| Accessibility | 3/4 | Automated axe checks return no violations at phone width, with named controls, visible focus and skip link. Physical screen-reader testing remains outside this review. |
| Performance | 3/4 | Local craft imagery, intrinsic image dimensions and no UI framework bundle. External fonts still require a network request. |
| Theming | 4/4 | Semantic tokens and `DESIGN.md` cover colour, type, shape, spacing and components. No dark mode is claimed. |
| Responsive design | 4/4 | 140 page, role and size combinations passed with no overflow, tiny inputs or broken references. No physical-device gesture certification is claimed. |
| Implementation integrity | 4/4 | Real database counts, original generated craft art, shared templates and preserved project constraints. |
| Total | 18/20 | Strong, with the stated testing limits. |

## Detector and refinements

The final Impeccable detector passes at 1280x800 return zero findings on:

- `/`
- `/products/`
- `/product/1/madhubani-lotus-wall-painting/`

Earlier iterations of the redesign produced small warnings. The final pass fixed the remaining actionable items:

- Narrowed the product description measure to 56ch so rendered lines stay readable.
- Added a visually hidden heading on the browse page instead of a decorative visible heading.
- Removed the leftover "Keep exploring" eyebrow from the related-products section.
- Fixed the phone hero order, the craft strip behaviour and the product-label clipping found during the responsive pass.

There are no detector waivers in the final state.

## Accessibility and verification

- Responsive and WCAG audit: 140 page, role and size combinations across 360x740, 390x844, 768x1024 and 1366x768. Result: 0 combinations needing attention.
- Axe at 390x844 with the WCAG 2.0 A, 2.0 AA and 2.1 AA tags: 0 violations.
- Django system check: no issues.
- Migration check: no changes.
- Full test suite: 93 tests passed.
- Forbidden dash scan: 0 hits.
- Navigation state check: collection, impact and request pages expose the expected `aria-current="page"` pill for visitors and signed-in buyers.

## Taste Skill and the finish gate

Taste Skill was used as a review reference for hierarchy, section rhythm, image treatment, hover feedback and copy. Its full finish gate is not claimed for this project. The gate expects an armed static build and a scripted hero entrance; adding that script would violate the project's no custom JavaScript constraint. No shader, 3D scene, artificial full-screen section or replacement photography was introduced to satisfy generic rules. The brief and the approved Selvedge world took precedence.

## Evidence

- Final desktop, tablet, phone and header captures are in `docs/ui_review/skills-review/`.
- Normalised detector and audit counts are in `docs/ui_review/skills-review/summary.json`.
- The full axe and responsive data is in `docs/ui_review/phase17/audit.json`.
- Raw third-party logs stayed in temporary development storage so their punctuation could not enter the project.

## Limits and next actions

- Automated checks do not replace a physical screen-reader or device pass.
- No performance benchmark or payment integration is claimed.
- The final SRS should use screenshots from this Selvedge interface, not the earlier cream direction.
- The report build remains blocked until the GitHub URL, deployed URL and report template are supplied.
