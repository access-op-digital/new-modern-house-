# Trade Professional — Modern House Numbers

Static replica of <https://www.modernhousenumbers.com/pages/trade>, deployed on
[Vercel](https://vercel.com). Zero build step — Vercel serves the HTML directly.

## Pages

| Path | File |
| --- | --- |
| `/` | `index.html` |
| `/trade` | same page, via a rewrite in `vercel.json` |


## Suggestion review mode

The page ships in Google-Docs-style review mode. Every proposed change is an
inline `<del>`/`<ins>` pair (or an `sg-new` block for whole new sections) tied to
a numbered card in the right-hand drawer by a shared `data-card` attribute.
Nothing is hard-coded in JS — to add a suggestion, add the mark and the card.

There are **two layers**, told apart by colour:

| Layer | Cards | Colour | Where it comes from |
| --- | --- | --- | --- |
| Brief | 1–17 | green | `Trade Landing Page Revisions — DRAFT 2026.09.03`, applied exactly as written |
| Search demand | 18–25 | blue | Ours. Headings whose wording has little or no search volume behind it, replaced with the term buyers use. DataForSEO, Google Ads, US, September 2026 |

Three toolbar modes:

- **Show suggestions** — both layers, full redline (default)
- **Brief only** — collapses the blue layer to the brief's wording, so the client
  can review what they asked for on its own
- **Preview final** — every suggestion accepted, no markup

Suggestions 18, 19 and 22 revise a heading the brief had already revised, so the
mark shows the chain: live wording struck, brief wording struck, new wording.

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
