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

# Page title, meta/social description and share image. Kept free of review
# counts and ratings on purpose: those change, the tags should not.
TITLE = "Modern House Numbers Reviews | Hear Directly from Our Customers"
DESC = ("Read Modern House Numbers reviews from our customers on Google, plus testimonials "
        "from architects, designers and builders who use our house numbers and plaques.")
OG_IMAGE = "https://cms.modernhousenumbers.com/assets/pro_header_gal_3.jpg"
OG_ALT = "Modern house numbers 2314 and the name Eugenia Hall in white on a dark brick wall"

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
    # Phone/tablet menu: the replica header hides its links under 900px.
    header = header.replace(
        '<nav class="nav-links" aria-label="Primary">',
        '<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">'
        '<span class="nav-toggle__bars" aria-hidden="true"></span><span class="visually-hidden">Menu</span></button>\n'
        '    <nav class="nav-links" id="primary-nav" aria-label="Primary">')
    assert 'id="primary-nav"' in header
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
        "@@TITLE@@": esc(TITLE), "@@DESC@@": esc(DESC),
        "@@OG_IMAGE@@": OG_IMAGE, "@@OG_ALT@@": esc(OG_ALT),
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

<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<link rel="canonical" href="https://www.modernhousenumbers.com/pages/testimonials">

<!-- Social share tags. og:url is the proposed live URL, like the canonical.
     The image is MHN's own photo on their public image server, so link
     previews can load it even though this preview deployment is protected. -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="Modern House Numbers">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESC@@">
<meta property="og:url" content="https://www.modernhousenumbers.com/pages/testimonials">
<meta property="og:image" content="@@OG_IMAGE@@">
<meta property="og:image:secure_url" content="@@OG_IMAGE@@">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="955">
<meta property="og:image:height" content="636">
<meta property="og:image:alt" content="@@OG_ALT@@">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="@@TITLE@@">
<meta name="twitter:description" content="@@DESC@@">
<meta name="twitter:image" content="@@OG_IMAGE@@">
<meta name="twitter:image:alt" content="@@OG_ALT@@">
<meta name="robots" content="noindex,nofollow">
<!-- Preview deployment: noindex. The canonical is the proposed live URL,
     which does not exist yet. -->

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@200;300;400;600;700&family=Mulish:wght@300;400;600;700&display=swap">

<style>
/* ============ MHN brand tokens, lifted from index.html ============ */
@@TOKENS@@
/* Layout follows the reference page; look and feel follows the live
   modernhousenumbers.com: thin Barlow headings, Muli body, square corners,
   #f0f0f0 and #393838 bands, orange pill buttons, uppercase tracked labels. */
:root{
  --star:#f36a10;
  --band:#f0f0f0;
  --charcoal:#393838;
  --hair:#dcdbdb;
  --on-dark:#f0f0f0;
  --on-dark-soft:#bdbcbc;
  --space-2:.5rem;--space-3:.75rem;--space-4:1rem;--space-5:1.5rem;--space-6:2rem;--space-7:3rem;--space-8:4.5rem;
  --content-width:1180px;
  --track:.12em;
}

*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:var(--body);font-size:16px;font-weight:400;line-height:1.5;color:var(--ink);
  background:#fff;-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}
a{color:var(--ink)}
.site-header a,.site-footer a,.crumbs a{text-decoration:none}
.crumbs a:hover{text-decoration:underline}
p{margin:0}
h1,h2,h3{font-family:var(--head);color:var(--ink);margin:0;line-height:1.2;font-weight:300;text-wrap:balance}
.visually-hidden{position:absolute!important;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
  clip:rect(0,0,0,0);white-space:nowrap;border:0}
.skip{position:absolute;left:-9999px}
.skip:focus{left:12px;top:12px;z-index:99;background:#fff;padding:.5rem .8rem;border:1px solid var(--ink)}

@@HEADER_CSS@@
.site-header .container{max-width:var(--maxw);margin:0 auto;padding:0 24px}

.container{width:min(100% - 48px,var(--content-width));margin-inline:auto}
@media(max-width:560px){.container{width:calc(100% - 36px)}}
.section{padding-block:var(--space-8)}
.section--white{background:var(--band)}
.lead{font-size:1rem;font-weight:300;color:var(--ink)}
.h2{font-size:clamp(1.6rem,1.2rem + 1.4vw,1.875rem);font-weight:300}

/* buttons: the live site's orange pill (Add to Cart) and outlined square (Shop Now) */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:var(--space-2);min-height:44px;
  padding:8px 32px;border:1px solid transparent;border-radius:9999px;font:inherit;font-size:.9375rem;
  font-weight:400;letter-spacing:var(--track);text-transform:uppercase;text-decoration:none;cursor:pointer;
  transition:background .15s,color .15s,border-color .15s}
.btn--primary{background:var(--orange);color:#fff}
.btn--primary:hover{background:var(--orange-dk);color:#fff}
.btn--lg{min-height:48px}
.btn:focus-visible,a:focus-visible{outline:2px solid var(--orange);outline-offset:2px}
.link-arrow{padding-block:var(--space-2);font-size:.875rem;font-weight:700;letter-spacing:var(--track);
  text-transform:uppercase;color:var(--ink);text-decoration:none}
.link-arrow:hover{color:var(--orange-dk)}
.stars{display:inline-flex;gap:2px}

/* hero */
.page-hero{padding-block:var(--space-5) var(--space-7)}
.crumbs ol{display:flex;flex-wrap:wrap;gap:6px;margin:0;padding:0;list-style:none;font-size:.75rem;
  letter-spacing:.08em;text-transform:uppercase;color:var(--ink-soft)}
.crumbs li+li::before{content:"\\203A";margin-right:6px;color:var(--ink-soft)}
.crumbs a{color:var(--ink-soft)}
.page-hero h1{font-size:clamp(2rem,1.4rem + 2.4vw,2.75rem);font-weight:200;margin:var(--space-5) 0 var(--space-3)}
.page-hero .lead{max-width:62ch}
@media(max-width:560px){.page-hero{padding-bottom:var(--space-6)}
  .score-row .btn,.commercial-head__actions .btn{width:100%;padding:8px 16px;font-size:.875rem;letter-spacing:.08em}
  .score{width:100%}}
.score-row{display:flex;flex-wrap:wrap;align-items:center;gap:var(--space-3) var(--space-5);margin-top:var(--space-5)}
.score{display:inline-flex;flex-wrap:wrap;align-items:center;gap:var(--space-2) var(--space-3);padding:10px 18px;
  border:1px solid var(--hair);color:var(--ink);font-size:.9375rem}
.score strong{font-family:var(--head);font-size:1.375rem;font-weight:600;line-height:1}

/* review wall: white tiles on the live site's grey band */
.wall{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:var(--space-4);margin:0;padding:0;list-style:none}
@media(max-width:360px){.wall{grid-template-columns:1fr}}
.review{display:flex;flex-direction:column;gap:var(--space-3);height:100%;margin:0;padding:var(--space-5);background:#fff}
.review__top{display:flex;justify-content:space-between;align-items:center;gap:var(--space-3)}
.review__source{font-family:var(--head);color:var(--ink);text-transform:uppercase;letter-spacing:.08em;
  font-size:.75rem;font-weight:700}
.review blockquote{display:flex;flex-direction:column;gap:var(--space-2);flex-grow:1;margin:0;color:var(--ink);
  font-size:.9375rem;font-weight:400;line-height:1.6;overflow-wrap:anywhere}
.review figcaption{padding-top:var(--space-3);border-top:1px solid var(--band);font-size:.8125rem;font-weight:700;
  letter-spacing:.04em}
.more-reviews{margin-top:var(--space-6);text-align:center}

/* trade testimonials: charcoal tiles, as the live site's dark bands */
.commercial-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;
  gap:var(--space-5) var(--space-7);margin-bottom:var(--space-6)}
.commercial-head>div:first-child{flex:1 1 560px}
.commercial-head .lead{margin-top:var(--space-3)}
.commercial-head__actions{display:flex;flex-wrap:wrap;align-items:center;gap:var(--space-3);color:var(--ink-soft);font-size:.9375rem}
.commercial-head__actions a:not(.btn){font-weight:700;color:var(--ink)}
.quotes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:var(--space-4);margin:0;padding:0;list-style:none}
@media(max-width:900px){.quotes{grid-template-columns:1fr}}
.quote{display:flex;flex-direction:column;gap:var(--space-4);height:100%;margin:0;padding:var(--space-6);
  background:var(--charcoal);color:#fff}
.quote svg{color:var(--orange)}
.quote blockquote{flex-grow:1;margin:0;color:var(--on-dark);font-weight:300;line-height:1.6}
.quote figcaption{display:flex;flex-direction:column;gap:2px;padding-top:var(--space-4);border-top:1px solid rgba(255,255,255,.14)}
.quote figcaption strong{font-family:var(--head);font-weight:700;font-size:.9375rem;letter-spacing:.06em;text-transform:uppercase}
.quote figcaption span{color:var(--on-dark-soft);font-size:.8125rem}

/* closing band: the live site's grey band */
.cta{background:var(--band);border-top:1px solid #e6e5e5}
.cta__inner{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:var(--space-5);padding-block:var(--space-7)}
.cta h2{font-size:clamp(1.6rem,1.2rem + 1.4vw,1.875rem);font-weight:300}
.cta__buttons{display:flex;flex-wrap:wrap;gap:var(--space-3)}
.cta__primary{background:var(--orange);color:#fff}
.cta__primary:hover{background:var(--orange-dk);color:#fff}
.cta__secondary{border:1px solid var(--ink);border-radius:0;color:var(--ink);font-weight:600}
.cta__secondary:hover{background:var(--ink);color:#fff}
.cta__creds{flex-basis:100%;padding-top:var(--space-4);border-top:1px solid var(--hair)}
.creds{display:flex;flex-wrap:wrap;gap:8px 28px;margin:0;padding:0;list-style:none;color:var(--ink);font-size:.8125rem;
  letter-spacing:.04em}
.creds li{display:flex;align-items:center;gap:8px}
.creds svg{flex:none;color:var(--orange)}
@media(max-width:560px){.cta__buttons,.cta__buttons .btn{width:100%}}

@@FOOTER_CSS@@
.site-footer .container{max-width:var(--maxw);width:auto;margin:0 auto;padding:0 24px}
.site-footer{background:var(--charcoal)}

/* ============ phone and tablet ============ */
.nav-toggle{display:none}
@media(max-width:900px){
  .site-header .nav{position:relative}
  .nav-toggle{display:inline-grid;place-items:center;flex:none;width:44px;min-width:44px;height:44px;margin-right:-8px;padding:0;
    background:none;border:0;cursor:pointer;color:var(--ink)}
  .nav-toggle__bars,.nav-toggle__bars::before,.nav-toggle__bars::after{display:block;width:22px;height:2px;
    background:currentColor;position:relative;transition:transform .2s,opacity .2s}
  .nav-toggle__bars::before,.nav-toggle__bars::after{content:"";position:absolute;left:0}
  .nav-toggle__bars::before{top:-7px}.nav-toggle__bars::after{top:7px}
  .nav-toggle[aria-expanded="true"] .nav-toggle__bars{background:transparent}
  .nav-toggle[aria-expanded="true"] .nav-toggle__bars::before{transform:translateY(7px) rotate(45deg)}
  .nav-toggle[aria-expanded="true"] .nav-toggle__bars::after{transform:translateY(-7px) rotate(-45deg)}
  .nav-links.is-open{display:flex;flex-direction:column;align-items:stretch;gap:0;position:absolute;
    top:100%;left:0;right:0;background:#fff;border-bottom:1px solid var(--line-soft);
    box-shadow:0 12px 24px rgba(0,0,0,.08);padding:4px 24px 12px}
  .nav-links.is-open a{display:flex;align-items:center;min-height:48px;border-top:1px solid var(--line-soft)}
  .nav-links.is-open a:first-child{border-top:0}
  /* trade quotes: two across on tablets, one on phones */
  .quotes{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:620px){.quotes{grid-template-columns:1fr}}
/* the full wall is 213 cards; every width loads it in steps so the closing
   band stays a short scroll away (18 = six rows of three on desktop) */
.js-steps .wall>li.is-later{display:none}
.wall-more{display:flex;justify-content:center;margin-top:var(--space-6)}
.wall-more .btn{background:#fff;border:1px solid var(--ink);border-radius:0;color:var(--ink);font-weight:600}
.wall-more .btn:hover{background:var(--ink);color:#fff}
.wall-more[hidden]{display:none}
.wall-more+.more-reviews{margin-top:var(--space-4)}
/* comfortable tap targets */
.link-arrow{display:inline-flex;align-items:center;min-height:44px}
.commercial-head__actions span a{display:inline-flex;align-items:center;min-height:44px}
@media(max-width:1023px){
  .foot-social{gap:2px;margin-left:-11px}
  .foot-social a{display:inline-grid;place-items:center;width:44px;height:44px}
  .foot-signup input{min-height:44px}
  .foot-signup button{min-height:44px}
  .foot-col ul{gap:0}
  .foot-col ul a{display:inline-flex;align-items:center;min-height:36px}
  .foot-legal a{display:inline-flex;align-items:center;min-height:32px}
  .crumbs a,.crumbs span{display:inline-flex;align-items:center;min-height:32px}
}
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
      <div class="wall-more" hidden><button type="button" class="btn" id="wall-more-btn">Read more reviews</button></div>
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

<script>
(function(){
  /* phone/tablet menu */
  var t=document.querySelector('.nav-toggle'), n=document.getElementById('primary-nav');
  if(t&&n){
    t.addEventListener('click',function(){
      var open=t.getAttribute('aria-expanded')!=='true';
      t.setAttribute('aria-expanded',open?'true':'false'); n.classList.toggle('is-open',open);
    });
    document.addEventListener('keydown',function(e){
      if(e.key==='Escape'&&n.classList.contains('is-open')){n.classList.remove('is-open');t.setAttribute('aria-expanded','false');t.focus();}
    });
  }
  /* review wall in steps: 18 at a time (rows of 3 or 2), 12 on phones */
  var STEP=window.matchMedia('(max-width:639px)').matches?12:18, items=[].slice.call(document.querySelectorAll('.wall>li')),
      box=document.querySelector('.wall-more'), btn=document.getElementById('wall-more-btn'), shown=STEP;
  if(!items.length||!box) return;
  document.documentElement.classList.add('js-steps');
  function render(){
    items.forEach(function(li,i){li.classList.toggle('is-later',i>=shown);});
    box.hidden=shown>=items.length;
  }
  btn.addEventListener('click',function(){
    var first=items[shown]; shown+=STEP; render();
    if(first){var a=first.querySelector('figure'); if(a){a.setAttribute('tabindex','-1'); a.focus({preventScroll:true});}}
  });
  render();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
