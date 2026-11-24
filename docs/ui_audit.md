# Virasat UI audit before Design System v2

> Historical record. This audit describes the interface before the Selvedge redesign. The current visual authority is `DESIGN.md`, and the final review is in `docs/skill_review.md`.

This audit records the problems visible in the templates and in the baseline screenshots in `docs/ui_review/before-phase13/`. The baseline covers 360x740, 768x1024 and 1366x768. The findings below drive Phases 13 to 17. This is an honest audit: it includes pages that work correctly but look unfinished.

## Shared shell

- The header fits at 1366 but becomes crowded at 360. Several links rely on small icons and short labels, and the sign-in action competes with the brand.
- The footer is a single flat row. It has no grouped navigation, no brand statement and no clear end to the page.
- The skip link exists, but the header, main and footer landmarks are not consistently used across every page.
- The visual language is mostly cream and white. There are no deliberate alternating bands, so long pages feel flat.
- All headings use Playfair Display. Body copy, buttons and numbers also inherit serif styles in places.
- Playfair Display old-style numerals make prices, statistics and step numbers look uneven. Dashboard counts such as 3, 0 and 1 appear as old-style figures, and prices use serif figures.
- Shadows and borders are almost identical on every card. There is no clear elevation scale.
- Hover, pressed and disabled states are missing or barely visible. Focus is present but inconsistent.
- Small labels use low-contrast warm brown on cream in several places.
- Buttons are below the 48px target in some header and card contexts.

## Home

- The hero heading sits inside a beige panel while the decorative pattern occupies the other half. The phrase "Craft carries a story" is laid over the pattern and visually collides with it.
- The hero has no search box, even though search is the primary browse action.
- The pattern is generic diamonds and lines. It does not show a craft, product or maker.
- The page has no trust bar, no artisan section, no market linkage band and no clear explanation for buyers versus artisans.
- Craft cards are small icon tiles, not rich cards with cover art and product counts.
- "Freshly added" cards have uneven heights. Some cards show the AI-assisted label and some do not, which creates noise.
- Cards show no artisan name, rating, wishlist action or add-to-cart action.
- The statistics band is a dark strip with three numbers and no context or link.
- "Recently viewed" is present only after browsing, which is correct, but it reuses the unfinished product card.
- The "How Virasat works" panel has three buyer steps only. Artisans are not addressed.
- The footer is sparse and does not help a visitor find key areas.

## Browse products

- The filter sidebar is very tall because every field has a helper sentence. Category, craft, state, price, verified and sort each add extra vertical space.
- Price From and To are stacked instead of sharing a row.
- On mobile the sidebar appears below the product grid, so a visitor must scroll past products to find filters.
- There is no offcanvas filter experience and no active-filter summary.
- The result count is plain text. There are no removable filter chips and no visible sort control above the grid.
- Empty results use a small icon and one line, without a helpful illustration or a strong reset action.
- Product images are the same repeated placeholder tile with only a colour change.
- Product cards have uneven heights because titles and labels wrap differently.
- Cards omit the artisan name, verified tick, rating, wishlist and add-to-cart action.
- The AI-assisted label appears on many cards even though the detail page is the correct place for that disclosure.
- The mobile filter link points to the page anchor, then the form is still far below the grid.

## Product detail

- The two columns are unbalanced. The image is large and the right column ends abruptly with a maker box.
- There is no breadcrumb component, only a thin trail of text.
- The only purchase action for a visitor is "Sign in to buy". There is no quantity selector for buyers.
- The page lacks trust points such as handmade, fair pay or cash on delivery.
- The artisan card has no avatar, verified badge or "View all pieces" link.
- Story, materials, care and reviews are separate blocks rather than a compact tabbed area.
- The AI disclosure is shown as a badge in the main column and competes with the verified badge.
- Reviews are a long stack of cards with no summary or count in the heading.
- There is no sticky mobile buy bar.
- Related products use the unfinished card and are labelled "More from this artisan", which is narrower than the requested related grid.

## Login and register

- On desktop the left half is mostly empty text while the form fills the right half.
- The mobile form is long. Register shows every Django username rule and the complete password-validator list.
- Login shows "The username you chose when you joined." and "Keep your password private." These do not help a returning user.
- Register uses a dropdown for role. The two roles deserve large, clear radio cards.
- State and city are stacked with no grouped layout.
- There is no collapsed password-help area.
- The auth card uses the same shadow and radius as every other surface, so the form has no focal status.

## Artisan dashboard

- The greeting is large but the useful actions are a row of similar buttons.
- Counts use Playfair old-style numerals and are hard to scan.
- The page has no icons for published, drafts, orders or matches.
- The earnings panel has no visual comparison of delivered and pending amounts.
- Recent products are a small grid with a status chip and an edit link, not a compact management list.
- Matching requests are mentioned in the navigation but not surfaced on the dashboard.
- Empty states are plain text with no action.

## AI smart-catalog flow

- The flow is labelled "Step 1 of 2" and "Step 2 of 2", not the requested three-step Describe, Review and Publish sequence.
- Step 1 is a long single card. Field labels are functional but not friendly, and placeholders do not show realistic examples.
- The AI button is labelled "Prepare my draft", which hides the fact that AI may be used.
- Step 2 shows one long form. English and Hindi are stacked with no side-by-side review.
- There is no preview of the future product card.
- The "AI draft, please review" alert is a generic Bootstrap info box.
- Save draft, publish and regenerate actions have similar visual weight.
- The regenerate confirmation is a block inside another card.

## My products

- The page is a stack of wide cards with a small status chip, title, price and stock.
- Actions crowd together. Publish requires a checkbox inside the action row.
- There are status tabs but no counts and no mobile-specific card layout.
- Status is shown as a small chip with no consistent tone mapping.
- Images are small landscape crops even though the catalog uses portrait art.

## Cart

- Line items are wide cards, not a clear list. The product image and controls compete.
- The order summary is not sticky on desktop.
- The fair-pay note is absent even though the platform fee matters to artisans.
- The quantity input and Update button sit inside a generic action row.
- The Remove button has the same visual weight as Update.
- Empty cart is a plain icon and one line.

## Checkout

- The form and summary are both cards with the same treatment.
- Payment methods are a default select or radio list with no explanation of the demo boundary.
- The UPI disclaimer is small text below all fields.
- The summary does not show artisan or fair-pay context.
- There is no clear two-column rhythm at desktop and no order summary heading hierarchy.

## Orders and artisan orders

- Order cards use a plain status word, not a coloured badge.
- The status path "Placed to Confirmed to Shipped to Delivered" is a single text line, not a timeline.
- The invoice action is a generic outline button.
- Artisan order cards contain the address, fair-pay breakdown and next action in one dense block.
- The fair-pay amounts are plain spans with no hierarchy.
- Empty states have no illustration or action.

## Requests and proposals

- Request cards show category and description but not days left, quantity emphasis or a budget badge.
- Match pages show "Match score n/5" with no strong or good match chip.
- Proposal cards show status, title, price and days but no clear artisan identity or accept hierarchy.
- My requests and my offers use the same plain card stack.
- Many empty states are a single sentence.

## Profile, wishlist and verification

- Profile summary is a plain card with a large initial circle.
- Verification actions are two buttons of similar weight.
- Wishlist reuses the old product card and has no saved count.
- Verification queue cards are wide and sparse, with no queue count.

## Error and offline pages

- Error pages use a generic icon and one heading. There is no small illustration and no secondary path other than home.
- The offline page is already branded, but it should use the final illustration and button system after the redesign.

## Partials and stylesheet structure

- `_form_field.html` prints every help text, including obvious ones.
- `_product_card.html` has no artisan, rating, wishlist or cart action and always prints the AI label.
- `_messages.html` is a plain Bootstrap alert without icons or a dismiss control.
- There is no reusable artisan card, craft card, stat, empty state, status badge, breadcrumb, page header, stepper or toast stack.
- `theme.css` has useful rules but no token layer. Colour and spacing values are repeated, old components are layered by later overrides, and typography does not isolate numerals.
- The stylesheet has no elevation scale, no semantic colour aliases, no consistent focus ring, no motion policy and no reduced-motion support.

## Baseline evidence

| Page | Baseline files |
| --- | --- |
| Home | `before-phase13/public-home-360.png`, `-768.png`, `-1366.png` |
| Browse | `before-phase13/public-products-360.png`, `-768.png`, `-1366.png` |
| Product detail | `before-phase13/public-detail-360.png`, `-768.png`, `-1366.png` |
| Login | `before-phase13/public-login-360.png`, `-768.png`, `-1366.png` |
| Register | `before-phase13/public-register-360.png`, `-768.png`, `-1366.png` |
| Cart | `before-phase13/buyer-cart-360.png`, `-768.png`, `-1366.png` |
| Checkout | `before-phase13/buyer-checkout-360.png`, `-768.png`, `-1366.png` |
| Requests | `before-phase13/buyer-requests-360.png`, `-768.png`, `-1366.png` |
| Artisan dashboard | `before-phase13/artisan-dashboard-360.png`, `-768.png`, `-1366.png` |
| Add a product | `before-phase13/artisan-product-new-360.png`, `-768.png`, `-1366.png` |

Phase 13 creates the token system and components. Phases 14 to 16 apply them to the public and signed-in pages, and Phase 17 closes the remaining responsive and accessibility gaps.
