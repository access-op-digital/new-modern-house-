# Trade Professional — Modern House Numbers

Static replica of <https://www.modernhousenumbers.com/pages/trade>, deployed on
[Vercel](https://vercel.com). Zero build step — Vercel serves the HTML directly.

## Pages

| Path | File |
| --- | --- |
| `/` | `index.html` |
| `/trade` | same page, via a rewrite in `vercel.json` |


## How the page renders

The page is the **final copy** — every revision from the brief is applied and
reads as finished text. The one exception is **headings**, which keep the cut so
the wording being replaced is still visible: struck old, new wording after it.

There is no toolbar, no drawer and no JS for any of this; it is CSS only. `.sg
del` is hidden by default and re-shown under `h1`/`h2`/`h3`. Body copy, intros
and the nine whole-new sections (`sg-new`) therefore render clean.

Headings carry two colours:

| Colour | Source |
| --- | --- |
| green | `Trade Landing Page Revisions — DRAFT 2026.09.03`, applied as written |
| blue | Ours — headings the brief left on wording with little or no search demand |

`data-card` attributes are kept on every mark. They drive nothing now, but they
are what a review drawer would hook back onto.

### The blue headings, and why

Volumes are DataForSEO, Google Ads, United States, September 2026.

| Heading | Replaces | Demand |
| --- | --- | --- |
| Modern House Numbers and Letters | brief's *Architectural Numbers + Letters* | 40 → **22,200** (*modern house numbers* 6,600) |
| Custom Address Plaques | brief's *Architectural Address Plaques* | 10 → **4,400** (*custom address signs* 1,000) |
| QuickShip House Numbers and Letters, Shipped Next Business Day | *QuickShip Numbers + Letters* | states the lead time the tab exists to answer |
| Restroom Signs in Solid Recycled Aluminum | *Architectural Restroom Signs* | no data → **12,100** |
| House Numbers and Signage by Property Type | brief's 76-char enumerating heading | stops listing the five rows directly beneath it |
| House Numbers and Building Numbers for Residential Projects | *1. Unit + Building Identification* | no data → **720** |
| Apartment Unit Numbers and Multifamily Building Signage | *2. Multifamily Signage* | 10 → **480** |
| Wayfinding / Monument / Room Number rows | *3.–5.* prefixed labels | 4,400 · 1,600 · 170 |

**Open before shipping:** *ADA restroom signs* draws 1,600 a month and is the
obvious next heading, but ADA signage needs tactile characters and Grade 2
Braille. This page describes stencil-cut aluminium only, so ADA stays out of the
heading until the product is confirmed to comply.

## Not indexed, on purpose

This page reproduces a live commercial page. If search engines indexed this copy
it would compete with the client's own URL, so the deployment is kept out of
search three ways:

- `<meta name="robots" content="noindex,nofollow">` in the page
- `X-Robots-Tag: noindex, nofollow` response header (`vercel.json`)
- `Disallow: /` in `robots.txt`

The page's `<link rel="canonical">` still points at the real URL. Remove all four
only if this ever becomes the canonical home of the page.

## What is and isn't live

The source page's configurator and trade signup post to Shopify/Klaviyo. This is
a static page, so both hand off to the real endpoints instead of faking a submit:

- the configurator deep-links to the product page with the chosen text, font,
  finish, height and orientation
- the trade form GETs to `/pages/trade-program-signup`

Brand tokens (`#393838`, `#f36a10`, Barlow 300, Mulish) are measured from the
live page. Imagery and the seven MHN typefaces load from the brand's own CDNs.

## Deploy

1. In Vercel, **Import** the `access-op-digital/new-modern-house-` repo.
2. Framework Preset: **Other** (static). Leave build & output settings empty.
3. Deploy. Every push to `main` auto-deploys.
