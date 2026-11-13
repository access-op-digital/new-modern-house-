"""Build pages/testimonials.html, laid out exactly like the reference page
https://cpiservice.com/reviews-and-testimonial/ (hero with a Google score
pill, one wall of Google review cards, a dark testimonial grid, a closing
band with credentials), in Modern House Numbers brand colours and fonts.

Run from the repo root:  python build/build_testimonials.py

Inputs (build/data/):
  gbp-reviews.json            Google Business Profile reviews of Modern House
                              Numbers (CID 5810350739318967915), pulled through
                              DataForSEO business_data/google/reviews.
  testimonials-snapshot.json  the testimonial carousel of the live
                              /pages/trade page (the trade testimonials).

Rules this script enforces:
  - Review wording is the Google text, untouched: only HTML-escaped and split
    into paragraphs on its own line breaks. Reviews with a star rating but no
    text are counted in the score but not shown, as Google itself does.
  - Reviewer names follow the reference page: first name plus last initial.
  - A review Google translated shows Google's English text, labelled as
    translated, which is how Google itself displays it.
  - The score pill uses the rating and review count Google reports for the
    profile, not a number computed here.
  - Header, footer and brand tokens are lifted from index.html.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "build" / "data"
OUT = ROOT / "pages" / "testimonials.html"
MAPS = "https://www.google.com/maps?cid=5810350739318967915"

# Trade testimonials: (name, role) split by hand from the live trade page's
# attribution lines, in the live carousel's order.
TRADE_WHO = [
    ("William Wunderlich", "Hakes Sash & Door"),
    ("Carson Arthur Design", "HGTV Canada"),
    ("Heather McGinnis", "Munro Homes, Canada"),
    ("Odyssey Construction, LLC", "Nashville"),
    ("Shaun Lockyer", "Shaun Lockyer Architects, Australia"),
    ("Beau Granger", "Beau Development, Seattle, WA"),
    ("Howard Hawkes & Kevin Kemper", "H3K Design, Palm Springs, CA"),
]

# Closing-band credentials. Every line is stated on the live site.
CREDS = [
    ("pin", "Handcrafted to order in Tucson, Arizona"),
    ("leaf", "Precision cut from solid recycled aluminum"),
    ("type", "Seven fonts, five finishes, sizes from 4″ to 15″"),
    ("tool", "Concealed hardware and a personalized drilling template"),
    ("flag", "Proudly made in USA"),
]

ICONS = {
    "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "leaf": '<path d="M5 19c0-8 5-13 15-14-1 10-6 15-14 15"/><path d="M5 19 13 11"/>',
    "type": '<path d="M5 6h14M12 6v13M9 19h6"/>',
    "tool": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L4 17l3 3 5.3-5.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    "flag": '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
}

STAR = ('<svg width="{s}" height="{s}" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l3.1 '
        '6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z" fill="{c}"/></svg>')
QUOTE = ('<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M7 7h4v6c0 3-2 4-4 4M15 7h4v6c0 3-2 4-4 4"/></svg>')


def esc(s):
    return html.escape(s, quote=True)


def stars(n, size):
    n = max(0, min(5, int(round(n))))
    return ('<span class="stars" role="img" aria-label="%d out of 5 stars">%s</span>'
            % (n, "".join(STAR.format(s=size, c="var(--star)" if i < n else "#d9d8d6") for i in range(5))))


BUSINESS = re.compile(r"(?i)\b(inc|llc|ltd|co|corp|group|real estate|homes|design|designs|construction|"
                      r"builders?|studio|architects?|properties|floors|carpets)\b\.?")


def short_name(full):
    """Reference-page style: first name + last initial ("Eric T."). Business
    names and single handles stay as Google shows them."""
    name = re.sub(r"\s*\([^)]*\)", "", (full or "")).strip()
    if not name:
        return "Google user"
    if BUSINESS.search(name):
        return name
    parts = name.split()
    if len(parts) == 1:
        return parts[0]
    last = parts[-1].strip(".")
    head = " ".join(parts[:-1]) if "&" in parts else parts[0]
    return "%s %s." % (head, last[0].upper()) if last else head


def load_gbp():
    raw = json.loads((DATA / "gbp-reviews.json").read_text(encoding="utf-8"))
    res = raw["result"][0]
    items = [i for i in (res.get("items") or []) if i.get("type") == "google_reviews_search"]
    shown, no_text = [], 0
    for it in items:
        text = (it.get("review_text") or "").strip()
        if not text:
            no_text += 1
            continue
        shown.append({
            "translated": bool(it.get("original_review_text")),
            "name": short_name(it.get("profile_name")),
            "rating": (it.get("rating") or {}).get("value") or 5,
            "paras": [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()],
        })
    return res, items, shown, no_text


def review_card(r):
    return ('<li><figure class="review"><div class="review__top">%s'
            '<span class="review__source">%s</span></div>'
            '<blockquote>%s</blockquote><figcaption>%s</figcaption></figure></li>'
            % (stars(r["rating"], 16),
               "Google review &middot; translated by Google" if r["translated"] else "Google review",
               "".join("<p>%s</p>" % esc(p) for p in r["paras"]), esc(r["name"])))


def quote_card(t, who):
    q = t["quote"].strip()
    return ('<li><figure class="quote">%s<blockquote>%s</blockquote>'
            '<figcaption><strong>%s</strong><span>%s</span></figcaption></figure></li>'
            % (QUOTE, esc(q), esc(who[0]), esc(who[1])))


def lift(src, start, end):
    i = src.index(start)
    j = src.index(end, i) + len(end)
    return src[i:j]


def main():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    tokens = lift(index, ":root{", "}\n")
    header_css = lift(index, "/* ---- header ---- */", "@media(max-width:900px){.nav-links{display:none}}")
    footer_css = lift(index, ".site-footer{", ".foot-legal a:hover{color:var(--orange)}")
    header = lift(index, '<header class="site-header">', "</header>")
    header = header.replace('<a href="/trade" aria-current="page">Trade</a>', '<a href="/trade">Trade</a>')
    footer = lift(index, '<footer class="site-footer">', "</footer>")

    res, items, shown, no_text = load_gbp()
    rating = res["rating"]["value"]
    votes = res["rating"]["votes_count"]
    trade = json.loads((DATA / "testimonials-snapshot.json").read_text(encoding="utf-8"))["trade"]
    assert len(trade) == len(TRADE_WHO)

    creds = "\n".join(
        '<li><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>'
        '<span>%s</span></li>' % (ICONS[k], esc(v)) for k, v in CREDS)

    page = TEMPLATE
    for key, val in {
        "@@TOKENS@@": tokens, "@@HEADER_CSS@@": header_css, "@@FOOTER_CSS@@": footer_css,
        "@@HEADER@@": header, "@@FOOTER@@": footer,
        "@@RATING@@": ("%.1f" % rating), "@@VOTES@@": "{:,}".format(votes),
        "@@SCORE_STARS@@": stars(rating, 22).replace('role="img" aria-label="5 out of 5 stars"', 'aria-hidden="true"'),
        "@@PULLED@@": raw_date(res),
        "@@REVIEWS@@": "\n".join(review_card(r) for r in shown),
        "@@QUOTES@@": "\n".join(quote_card(t, w) for t, w in zip(trade, TRADE_WHO)),
        "@@CREDS@@": creds, "@@MAPS@@": MAPS,
    }.items():
        page = page.replace(key, val)
    leftover = re.findall(r"@@[A-Z_]+@@", page)
    assert not leftover, leftover

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print("wrote", OUT.relative_to(ROOT), "%d bytes" % len(page.encode("utf-8")))
    print("google profile: rating %s from %s reviews; fetched %d, shown %d, rating-only %d"
          % (rating, votes, len(items), len(shown), no_text))


def raw_date(res):
    return (res.get("datetime") or "")[:10]


TEMPLATE = """<!DOCTYPE html>
<!--
  ============================================================================
  REVIEWS AND TESTIMONIALS, Modern House Numbers
  Proposed new page. There is no /pages/testimonials on the live site yet.
  GENERATED by build/build_testimonials.py from build/data/*.json. Do not edit
  this file by hand; change the script or the data and re-run it.

  Layout: an exact structural match of cpiservice.com/reviews-and-testimonial
  (page hero + Google score pill, one review wall, dark testimonial grid,
  closing band with credentials), in MHN brand colours and type.
  Reviews: Modern House Numbers' Google Business Profile, pulled @@PULLED@@,
  text untouched. Trade testimonials: the live /pages/trade carousel.
  No Review or AggregateRating markup, on purpose.
  ============================================================================
-->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Modern House Numbers Reviews | Hear Directly from Our Customers</title>
<meta name="description" content="Read Modern House Numbers reviews from our customers on Google, plus testimonials from architects, designers and builders who use our house numbers and plaques.">
<link rel="canonical" href="https://www.modernhousenumbers.com/pages/testimonials">
<meta name="robots" content="noindex,nofollow">
<!-- Preview deployment: noindex. The canonical is the proposed live URL,
     which does not exist yet. -->

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&family=Mulish:wght@400;600;700&display=swap">

<style>
/* ============ MHN brand tokens, lifted from index.html ============ */
@@TOKENS@@
/* reference-page scale and shapes, MHN colours */
:root{
  --star:#f36a10;
  --tint:#f7f6f4;
  --card-line:#e4e2df;
  --muted-on-dark:#d9d7d4;
  --accent-on-dark:#f7a368;
  --space-2:.5rem;--space-3:.75rem;--space-4:1rem;--space-5:1.5rem;--space-6:2rem;--space-7:3rem;--space-8:5rem;
  --content-width:1240px;
  --text-md:1.0625rem;
  --text-2xl:clamp(1.75rem,1.3rem + 1.8vw,2.5rem);
  --text-3xl:clamp(2.25rem,1.5rem + 3vw,3.375rem);
  --radius-sm:12px;
}

*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:var(--body);font-size:16px;line-height:1.6;color:var(--ink);
  background:var(--tint);-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}
a{color:var(--ink)}
.site-header a,.site-footer a,.crumbs a{text-decoration:none}
.crumbs a:hover{text-decoration:underline}
p{margin:0}
h1,h2,h3{font-family:var(--head);color:var(--ink);margin:0;line-height:1.15;text-wrap:balance}
.visually-hidden{position:absolute!important;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
  clip:rect(0,0,0,0);white-space:nowrap;border:0}
.skip{position:absolute;left:-9999px}
.skip:focus{left:12px;top:12px;z-index:99;background:#fff;padding:.5rem .8rem;border:1px solid var(--ink)}

@@HEADER_CSS@@
.site-header .container{max-width:var(--maxw);margin:0 auto;padding:0 24px}

.container{width:min(100% - 2 * var(--space-5),var(--content-width));margin-inline:auto}
@media(max-width:560px){.container{width:calc(100% - 2 * var(--space-4))}}
.section{padding-block:var(--space-8)}
.section--white{background:#fff}
.lead{font-size:var(--text-md);color:var(--ink-soft)}
.h2{font-size:var(--text-2xl);font-weight:600;letter-spacing:-.01em}

.btn{display:inline-flex;align-items:center;justify-content:center;gap:var(--space-2);min-height:48px;
  padding:0 var(--space-5);border-radius:var(--radius-sm);border:0;font:inherit;font-weight:700;
  text-decoration:none;cursor:pointer}
.btn--primary{background:var(--orange);color:#fff}
.btn--primary:hover{background:var(--orange-dk);color:#fff}
.btn--lg{min-height:56px;font-size:var(--text-md)}
.btn:focus-visible,a:focus-visible{outline:2px solid var(--orange);outline-offset:2px}
.link-arrow{padding-block:var(--space-2);font-weight:700;color:var(--orange-dk);text-decoration:none}
.link-arrow:hover{text-decoration:underline}
.stars{display:inline-flex;gap:2px}

/* hero */
.page-hero{padding-block:var(--space-5) var(--space-7)}
.crumbs ol{display:flex;flex-wrap:wrap;gap:6px;margin:0;padding:0;list-style:none;font-size:.8125rem;color:var(--ink-soft)}
.crumbs li+li::before{content:"\\203A";margin-right:6px;color:var(--ink-soft)}
.crumbs a{color:var(--ink-soft)}
.page-hero h1{font-size:var(--text-3xl);font-weight:600;letter-spacing:-.02em;margin:var(--space-4) 0 var(--space-3)}
@media(max-width:560px){.page-hero{padding-bottom:var(--space-6)}.page-hero h1{font-size:2rem}}
.score-row{display:flex;flex-wrap:wrap;align-items:center;gap:var(--space-3) var(--space-4);margin-top:var(--space-5)}
.score{display:inline-flex;align-items:center;gap:var(--space-3);background:#fff;border:1px solid var(--card-line);
  border-radius:999px;padding:10px 20px;color:var(--ink)}
.score strong{font-size:1.25rem}

/* review wall */
.wall{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:var(--space-4);margin:0;padding:0;list-style:none}
@media(max-width:360px){.wall{grid-template-columns:1fr}}
.review{display:flex;flex-direction:column;gap:var(--space-3);height:100%;margin:0;padding:var(--space-5);
  background:#fff;border:1px solid var(--card-line);border-radius:20px}
.review__top{display:flex;justify-content:space-between;align-items:center;gap:var(--space-3)}
.review__source{color:var(--ink-soft);text-transform:uppercase;letter-spacing:.08em;font-size:.75rem;font-weight:700}
.review blockquote{display:flex;flex-direction:column;gap:var(--space-2);flex-grow:1;margin:0;color:#333;
  font-size:.9375rem;overflow-wrap:anywhere}
.review figcaption{color:var(--ink);font-weight:700}
.more-reviews{margin-top:var(--space-5);text-align:center;font-weight:700}

/* trade testimonials */
.commercial-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;
  gap:var(--space-5) var(--space-7);margin-bottom:var(--space-6)}
.commercial-head>div:first-child{flex:1 1 560px}
.commercial-head .lead{margin-top:var(--space-3)}
.commercial-head__actions{display:flex;flex-wrap:wrap;align-items:center;gap:var(--space-3);color:var(--ink-soft)}
.commercial-head__actions a:not(.btn){font-weight:700}
.quotes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--space-4);margin:0;padding:0;list-style:none}
@media(max-width:900px){.quotes{grid-template-columns:1fr}}
.quote{display:flex;flex-direction:column;gap:var(--space-4);height:100%;margin:0;padding:var(--space-6);
  background:var(--ink);color:#fff;border-radius:20px}
.quote svg{color:var(--orange)}
.quote blockquote{flex-grow:1;margin:0;color:var(--muted-on-dark)}
.quote figcaption{display:flex;flex-direction:column}
.quote figcaption span{color:var(--accent-on-dark);font-size:.875rem}

/* closing band */
.cta{background:var(--orange)}
.cta__inner{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:var(--space-5);padding-block:var(--space-7)}
.cta h2{color:#fff;font-size:var(--text-2xl);font-weight:600}
.cta__buttons{display:flex;flex-wrap:wrap;gap:var(--space-3)}
.cta__primary{background:var(--ink);color:#fff}
.cta__primary:hover{background:#000;color:#fff}
.cta__secondary{border:2px solid #fff;color:#fff}
.cta__secondary:hover{background:rgba(255,255,255,.14);color:#fff}
.cta__creds{flex-basis:100%;padding-top:var(--space-4);border-top:1px solid rgba(255,255,255,.3)}
.creds{display:flex;flex-wrap:wrap;gap:8px 24px;margin:0;padding:0;list-style:none;color:rgba(255,255,255,.95);font-size:14px}
.creds li{display:flex;align-items:center;gap:8px}
.creds svg{flex:none}
@media(max-width:560px){.cta__buttons,.cta__buttons .btn{width:100%}}

@@FOOTER_CSS@@
.site-footer .container{max-width:var(--maxw);width:auto;margin:0 auto;padding:0 24px}
</style>
</head>
<body>

<a class="skip" href="#main">Skip to content</a>

@@HEADER@@

<main id="main">

  <section class="page-hero">
    <div class="container">
      <nav class="crumbs" aria-label="Breadcrumb">
        <ol>
          <li><a href="https://www.modernhousenumbers.com">Home</a></li>
          <li><a href="https://www.modernhousenumbers.com/pages/our-story">About</a></li>
          <li><span aria-current="page">Reviews</span></li>
        </ol>
      </nav>
      <h1>Modern House Numbers Reviews: Hear Directly from Our Customers</h1>
      <p class="lead">Homeowners, designers and builders share what it was like to order and install their house
        numbers. Read what our customers have to say about their experience with Modern House Numbers.</p>
      <div class="score-row">
        <p class="score">@@SCORE_STARS@@<span><strong>@@RATING@@</strong> out of 5 from @@VOTES@@ Google reviews</span></p>
        <a class="btn btn--primary" href="@@MAPS@@" target="_blank" rel="noopener">Read all our Google reviews
          <span class="visually-hidden">(opens Google Maps in a new tab)</span></a>
      </div>
    </div>
  </section>

  <section class="section section--white">
    <div class="container">
      <h2 class="visually-hidden">Customer reviews</h2>
      <ul class="wall">
@@REVIEWS@@
      </ul>
      <p class="more-reviews"><a class="link-arrow" href="@@MAPS@@" target="_blank" rel="noopener">See all @@VOTES@@ reviews on Google &rarr;<span class="visually-hidden">(opens in a new tab)</span></a></p>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="commercial-head">
        <div>
          <h2 class="h2">Trade Testimonials from Architects, Designers and Builders</h2>
          <p class="lead">Hear directly from the design and building professionals who use Modern House Numbers
            on their projects.</p>
        </div>
        <div class="commercial-head__actions">
          <a class="btn btn--primary" href="https://www.modernhousenumbers.com/pages/contact">Contact Us</a>
          <span>or <a href="https://www.modernhousenumbers.com/pages/trade">join the Trade Program</a></span>
        </div>
      </div>
      <ul class="quotes">
@@QUOTES@@
      </ul>
    </div>
  </section>

  <section class="cta">
    <div class="container cta__inner">
      <h2>Ready to order your house numbers?</h2>
      <div class="cta__buttons">
        <a class="btn btn--lg cta__primary" href="https://www.modernhousenumbers.com/products/house-numbers-letters">Shop Numbers + Letters</a>
        <a class="btn btn--lg cta__secondary" href="https://www.modernhousenumbers.com/products/plaque">Shop Plaques</a>
        <a class="btn btn--lg cta__secondary" href="https://www.modernhousenumbers.com/pages/contact">Contact Us</a>
      </div>
      <div class="cta__creds">
        <ul class="creds">
@@CREDS@@
        </ul>
      </div>
    </div>
  </section>

</main>

@@FOOTER@@

</body>
</html>
"""

if __name__ == "__main__":
    main()
