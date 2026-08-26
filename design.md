# EstateOS — Design System

_Last updated: 2026-08-26_

This is the reference for EstateOS's visual identity — the "why" behind every color, typeface, and layout
decision on the site. When in doubt about a new UI element, it should trace back to something in this
document.

---

## 1. Brand

**Name:** EstateOS

**Positioning (working copy):**
> A place to come home to. Quality lots and ready-to-build subdivisions across Cagayan Valley — built for
> the families staking their future here, whether they're planting roots for the first time, investing from
> abroad, or building something to grow into.

**Personality:** Warm & family-first. Not corporate-distant, not flashy-luxury. The tone of someone who
grew up in the valley and is proud to sell land in it — trustworthy without being stiff.

**Audience:**
- OFWs investing in property back home
- Young professionals buying their first home
- Investors looking for land in a growing region

**Where it's grounded:** Tuguegarao City, Cagayan Valley, Philippines. The site should read as distinctly
*of* this place — not a generic, could-be-anywhere real estate template.

---

## 2. Color — "Sun-Baked"

A dark, warm palette. The brief asked for a gray/dark theme, but "warm & family-first" pulls against the
cold, corporate mood dark UIs usually default to — the fix is warm-toned charcoal (brown-based, not
blue-based) instead of slate gray, plus one genuinely warm accent tied to the region rather than an
arbitrary brand color.

| Token | Hex | Role |
|---|---|---|
| `ink` | `#262220` | Primary dark surface — page background, nav, cards on dark |
| `clay` | `#4A4038` | Secondary dark surface — raised cards, hover states, borders on dark |
| `marigold` | `#D68A3E` | Primary accent — CTAs, links, active states, key highlights. Use deliberately, not everywhere |
| `sand` | `#A69A82` | Muted text, borders, disabled states, secondary UI on dark |
| `cream` | `#F5EFE4` | Text on dark surfaces, light-surface backgrounds where needed |
| `sage` (semantic) | `#7A8B6F` | Success states — muted olive, not a bright system green |
| `rust` (semantic) | `#9B4A3A` | Error/danger states — deep brick-red, distinguishable from marigold |

**Usage principles:**
- `ink` is the default background, not white. Light surfaces (`cream`) are the exception, used for
  content that needs to feel airy (e.g., a listing photo card), not the default.
- `marigold` is a spotlight, not a wash — one CTA per view, not five orange buttons.
- Never use pure black (`#000`) or pure white (`#FFF`) anywhere — everything should carry the warm
  undertone, even at the extremes.
- **Accessibility:** `cream` text on `ink` background is the primary reading pair and meets WCAG AA
  comfortably. `sand` on `ink` is for secondary/muted text only — check contrast before using it for
  anything load-bearing (labels, primary body copy).

**Implementation note:** be careful this doesn't drift toward the generic "warm cream background +
terracotta accent" look that's become an AI-design cliché — the difference here is structural (dark
surface first, cream is the exception not the base) and the accent hue is a yellower marigold, not a
red-leaning terracotta. Keep it that way.

---

## 3. Typography

| Role | Typeface | Notes |
|---|---|---|
| Display / headings | **Fraunces** | Warm, slightly irregular serif — real character without going full antique-luxury. This carries the brand's personality; use its optical sizing for large headings |
| Body / UI | **Work Sans** | Clean, highly legible, warmer and rounder than Inter. Carries the information-dense parts of the site (listings, forms, tables) |
| Data / utility | **IBM Plex Mono** | Prices, areas, dates, reference numbers — anywhere a number needs to read as precise and real |

**Type scale principle:** because the site is meant to be information-rich rather than spacious, resist
oversized hero type just for drama — Fraunces should feel confident at moderate sizes, not enormous.
Body copy and data should default smaller/denser than a typical minimal marketing site, closer to a
real estate portal's information density.

---

## 4. Layout & Spacing

**Direction: denser, information-rich** — not the spacious/minimalist default. This is a site where people
compare lots, prices, and terms; showing more at once is a feature, not a compromise.

- Tighter spacing scale than a typical marketing site — less air between cards, more listings visible
  per screen.
- Cards and tables should feel purposeful and dense without becoming cramped — the goal is a good real
  estate portal (Zillow-density), not a spreadsheet.
- Reserve generous whitespace for the few moments that deserve it (the hero, a single featured listing) —
  contrast makes density elsewhere feel intentional rather than just "no design happened."

---

## 5. Signature element — the Sierra Madre horizon

The one visual element the site should be remembered by: a **horizon silhouette of the Sierra Madre**
mountain range, the real range visible from Tuguegarao/Cagayan Valley.

**How to keep it specific, not generic:** a lot of sites use a vague "mountain icon" as decoration — the
difference here is using the Sierra Madre's actual silhouette proportions (long, layered ridgelines, not
a symmetrical triangle-peak cliché) so it reads as an actual place, not a stock landscape icon.

**Where it shows up:**
- A subtle line-art ridgeline low in the hero section, behind/beneath the headline — `sand` or `clay` on
  `ink`, low-contrast, atmosphere rather than illustration.
- A recurring thin divider motif in the footer, echoing the same ridgeline at small scale.
- Optionally: a loading/empty-state moment (e.g., "no lots match your search yet") using the silhouette
  rather than a generic empty-box icon.

Keep it to one quiet, consistent motif — not a mountain graphic on every page. Its power is in restraint
and repetition, not coverage.

---

## 6. Photography & imagery

Reference point: actual lots and subdivision houses — the real product, not aspirational lifestyle stock
photography (no staged families in generic modern kitchens). Documentary-leaning: real light, real land,
real streets. This supports the "warm & family-first, trustworthy" personality better than glossy staging
would, and it's honest about what's actually being sold — land and homes in a specific place, not a
lifestyle fantasy.

---

## 7. Voice & tone

- Plain, warm, direct — the way someone from the valley would talk about it, not corporate real-estate
  copy ("Discover your dream home today!").
- Specific over clever: name the place, the terms, the real numbers. Avoid vague aspirational language.
- Active voice, plain verbs. A button that says "Reserve this lot" should lead to a confirmation that says
  "Lot reserved" — not "Submission successful."

---

## 8. Open questions / not yet decided

- Exact logo/wordmark treatment for "EstateOS" (Fraunces-based wordmark is the likely direction, not
  yet drawn).
- Whether the Sierra Madre motif extends into the admin panel (staff-facing) or stays public-site-only —
  current lean is public-site-only, since the admin panel is a working tool, not a brand moment.
