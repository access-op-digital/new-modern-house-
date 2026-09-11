# Trade Professional — Modern House Numbers

Static replica of <https://www.modernhousenumbers.com/pages/trade>, deployed on
[Vercel](https://vercel.com). Zero build step — Vercel serves the HTML directly.

## Pages

| Path | File |
| --- | --- |
| `/` | `index.html` |
| `/trade` | same page, via a rewrite in `vercel.json` |

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
