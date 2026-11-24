---
name: Virasat
description: A forest and sage storefront for Indian handmade craft.
colors:
  primary: "#193A2A"
  primary-deep: "#112C1E"
  sage: "#DBE6BC"
  linen: "#F5F7EF"
  surface: "#FFFFFF"
  text: "#233B2E"
  text-muted: "#596653"
  border: "#DCE2D4"
  border-strong: "#B8C4AB"
  success: "#2F633D"
  warning: "#8A5608"
  danger: "#A52721"
typography:
  display:
    fontFamily: "Manrope, Noto Sans Devanagari, sans-serif"
    fontSize: "4.5rem"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.045em"
  heading:
    fontFamily: "Manrope, Noto Sans Devanagari, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  body:
    fontFamily: "Manrope, Noto Sans Devanagari, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "0em"
  label:
    fontFamily: "Manrope, Noto Sans Devanagari, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0.08em"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  pill: "999px"
spacing:
  one: "4px"
  two: "8px"
  three: "12px"
  four: "16px"
  five: "24px"
  six: "32px"
  seven: "48px"
  eight: "72px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.linen}"
    rounded: "{rounded.sm}"
    padding: "14px 24px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
    textColor: "{colors.linen}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "14px 24px"
    height: "48px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: "12px 14px"
    height: "48px"
---

## Overview

Virasat is a marketplace for Indian handmade craft. The storefront is quiet, tactile and direct: forest ink on a soft linen ground, sage fields behind original product art, and one confident object at a time. It should feel like a careful contemporary craft shop, not a heritage theme park or a generic startup template.

The product owns the colour. Interface surfaces stay neutral so the generated craft art provides the warmth and variation.

## Colors

Forest `#193A2A` is the primary ink, button fill and dark band. `#112C1E` is its pressed and hover depth. Sage `#DBE6BC` is a field colour behind featured work, never a body background. Linen `#F5F7EF` is the page ground. White is reserved for cards, labels and form fields that need separation from the ground.

Text is `#233B2E`; secondary text is `#596653`. Borders use `#DCE2D4` with `#B8C4AB` for interactive edges. Success, warning and danger keep their existing semantic meanings and are used only for status, never decoration.

Do not reintroduce terracotta, indigo or turmeric as visible interface colours. The old token names remain in CSS only as aliases so older components resolve to the forest system.

## Typography

Manrope carries every size: display, headings, body, labels and numbers. Noto Sans Devanagari supports Hindi passages. The display face is the same family at weight 600 with tight tracking, so hierarchy comes from scale and spacing rather than a second typeface.

Headings are upright, never italic. Body text sits between 65 and 75 characters per line. Numerals use lining tabular figures where prices and counts need to align. Small labels are at least 12px and use 0.08em tracking sparingly.

## Layout

The shell uses a 1360px container with fluid gutters. The home first viewport is a two-column split: copy, search and real marketplace figures on linen, then one large craft piece on a sage field with a white product label. Below 991px the split stacks, with copy first and the image second.

Craft navigation is a single forest band. It scrolls horizontally on phones without hiding the section itself. Product grids use four columns on wide screens, three on tablets and two on phones. Forms and reading pages stay narrower than commerce grids.

Space above a section heading is larger than the space below it. Sections are separated by 72px on desktop and 48px on phones. Cards use 24px internal padding; compact rows use 16px.

## Elevation & Depth

Depth is restrained. Most product and craft cards are flat on the page ground. White surfaces use a 1px border and, when lifted, a soft forest-tinted shadow with an offset blur. The featured product label may use the medium shadow because it sits over artwork.

No glow, coloured halo or floating glass panel is part of the system.

## Shapes

Corners are quiet: 8px for in-page buttons, inputs and media frames, 12px for cards, and 16px for large bands. Pills are reserved for the header navigation capsule, header actions, stamps, chips and status badges. Images are not circles. Product media uses a 4:5 frame; craft and artisan media use 16:10 or 1:1 depending on the source.

## Components

Primary buttons are solid forest with linen text and a 48px minimum height. Secondary buttons are transparent with a forest border and forest text. Destructive actions use text or outline treatment rather than a filled red block except in an explicit confirmation step.

Product cards are image, craft chip, maker, title, price and the relevant action. They have no surrounding card border on the storefront. The image is the dominant element and the title receives a 44px touch target on phones.

Inputs and selects are white with a visible border, 16px text on phones and a forest focus ring. Quantity selects stay compact but never below 44px in height.

The header is a sticky linen band closed by a dashed seam. The brand pairs the wordmark with a circular maker seal: a forest V inside a dotted stitch ring, with a small sage dot at the base. On hover or keyboard focus the stitch ring turns sixty degrees and the dot deepens to forest, so the mark feels handled rather than animated for its own sake. Navigation sits in a white pill capsule; the current page becomes a solid forest pill through `aria-current="page"`, and cart, account and menu controls use matching pills. The header call to action is the only solid forest pill in the bar, with a small outbound arrow.

The footer is forest with linen text and grouped shop, people and trust columns. It repeats the maker seal at a smaller size. The featured product label is a white block with the title, maker, region and price.

## Do's and Don'ts

Do let one real piece occupy a large frame. Do use the product's own material and palette as the visual interest. Do keep shopping actions obvious and labels factual. Do preserve the no-key and no-custom-JavaScript constraints.

Don't add decorative illustration behind product photography. Don't invent testimonials, maker portraits, guarantees or live payment claims. Don't use multiple accent colours in one view. Don't turn every element into a rounded card. Don't use em dashes or en dashes in any interface copy.
