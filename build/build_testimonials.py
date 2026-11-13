"""Build pages/testimonials.html from the review and testimonial snapshots.

Run from the repo root:  python build/build_testimonials.py

Inputs (build/data/):
  reviews-snapshot.json       every review returned by the live site's own
                              endpoint, cms.modernhousenumbers.com/reviews.php,
                              for the five product keys the product pages use.
  testimonials-snapshot.json  the testimonial carousels of the live homepage
                              and the live /pages/trade page.

Rules this script enforces:
  - Review and testimonial wording is never edited. Text is only unescaped,
    stripped of its <p>/<br> wrappers and re-escaped.
  - Header, footer and brand tokens are lifted from index.html so the page
    cannot drift from the trade replica.
  - No rating average is printed. The endpoint reports a fixed 4.5 that the
    reviews it returns do not add up to, so only counts are shown.
"""
import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "build" / "data"
OUT = ROOT / "pages" / "testimonials.html"
SITE = "https://www.modernhousenumbers.com"
PAGE_SIZE = 12

# product key -> (label shown on the card and filter, live product URL)
PRODUCTS = {
    "numbers": ("Numbers + Letters", SITE + "/products/house-numbers-letters"),
    "plaque": ("Plaques", SITE + "/products/plaque"),
    "mailbox": ("Mailbox Numbers + Letters", SITE + "/products/mailbox-numbers-letters"),
    "quickship": ("QuickShip", SITE + "/products/quick-ship"),
    "stencil": ("Curb Stencil", SITE + "/products/curb-stencil"),
}

# Homepage carousel entries that are homeowners. The other four homepage
# entries are trade customers and appear in the trade section, in the fuller
# wording the live trade page uses.
HOMEOWNERS = ["Kristen G.", "Melissa, Townsville AUS", "Nancy C., Minneapolis MN",
              "Julie and Stacey", "Allison, Chicago IL", "Gerry W."]


def esc(s):
    return html.escape(s, quote=True)


def paragraphs(raw):
    """Review HTML (only <p> and <br>) -> list of escaped paragraph strings."""
    out = []
    for part in re.split(r"(?i)</p>", raw):
        part = re.sub(r"(?i)<br\s*/?>", "\n", part)
        part = html.unescape(re.sub(r"<[^>]+>", "", part)).strip()
        if part:
            out.append("<br>".join(esc(line.strip()) for line in part.split("\n") if line.strip()))
    return out


def parse_date(s):
    try:
        d = datetime.strptime(s, "%b %d, %Y")
        return d if d.year >= 2000 else None
    except ValueError:
        return None


def stars(n):
    return ('<span class="stars" role="img" aria-label="%d out of 5 stars">'
            '<span aria-hidden="true">%s<i>%s</i></span></span>'
            % (n, "★" * n, "★" * (5 - n)))


def load_reviews():
    snap = json.loads((DATA / "reviews-snapshot.json").read_text(encoding="utf-8"))
    seen, rows, dropped = set(), [], 0
    for key in PRODUCTS:
        for r in snap["products"][key]["reviews"]:
            paras = paragraphs(r["review"])
            name = html.unescape(r["name"]).strip()
            ident = (name.lower(), " ".join(paras).lower())
            if paras and ident in seen:
                dropped += 1
                continue
            seen.add(ident)
            rows.append({
                "key": key, "id": r["id"], "rating": int(r["rating"]),
                "title": html.unescape(r["title"]).strip(), "paras": paras,
                "name": name, "location": html.unescape(r["location"]).strip(),
                "date": parse_date(r["date"]), "date_text": r["date"],
            })
    rows.sort(key=lambda r: (r["date"] or datetime(1900, 1, 1), int(r["id"])), reverse=True)
    return snap, rows, dropped


def review_card(r, index):
    label = PRODUCTS[r["key"]][0]
    who = []
    if r["name"]:
        who.append('<span class="rv-name">%s</span>' % esc(r["name"]))
    meta = [esc(x) for x in (r["location"], r["date_text"] if r["date"] else "") if x]
    if meta:
        who.append('<span class="rv-meta">%s</span>' % " &middot; ".join(meta))
    body = "".join("<p>%s</p>" % p for p in r["paras"])
    return (
        '<figure class="rv%s" data-product="%s">'
        '<div class="rv-top">%s<span class="rv-src">%s</span></div>'
        '<blockquote><p class="rv-title">%s</p>%s</blockquote>'
        '<figcaption>%s</figcaption></figure>'
        % (" rv-later" if index >= PAGE_SIZE else "", r["key"], stars(r["rating"]),
           esc(label), esc(r["title"]), body, "".join(who))
    )


def clean_who(s):
    return re.sub(r"^\s*-\s*", "", s).strip()


def img_url(u):
    return "https:" + u if u.startswith("//") else u


def story_card(t):
    return (
        '<figure class="story"><img src="%s" alt="Customer photo of a Modern House Numbers install" '
        'width="700" height="320" loading="lazy">'
        '<blockquote><p class="story-title">%s</p><p>%s</p></blockquote>'
        '<figcaption>%s</figcaption></figure>'
        % (esc(img_url(t["img"])), esc(t["title"]), esc(t["quote"]), esc(clean_who(t["who"])))
    )


def trade_card(t):
    who = clean_who(t["who"])
    credit = '<p class="tt-credit">%s</p>' % esc(t["caption"]) if t["caption"] else ""
    return (
        '<figure class="tt"><img src="%s" alt="Project photo from %s" width="700" height="320" loading="lazy">'
        '<div class="tt-body"><span class="tt-mark" aria-hidden="true">”</span>'
        '<blockquote><p>%s</p></blockquote><figcaption>%s</figcaption>%s</div></figure>'
        % (esc(img_url(t["img"])), esc(who), esc(t["quote"]), esc(who), credit)
    )


def lift(src, start, end):
    i = src.index(start)
    j = src.index(end, i) + len(end)
    return src[i:j]


def main():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    tokens = lift(index, ":root{", "}\n")
    base = lift(index, "*{box-sizing:border-box}", ".btn--sm{")
    base = base[: base.rindex(".btn--sm{")]
    header_css = lift(index, "/* ---- header ---- */", "@media(max-width:900px){.nav-links{display:none}}")
    footer_css = lift(index, ".site-footer{", ".foot-legal a:hover{color:var(--orange)}")
    header = lift(index, '<header class="site-header">', "</header>")
    header = header.replace('<a href="/trade" aria-current="page">Trade</a>', '<a href="/trade">Trade</a>')
    footer = lift(index, '<footer class="site-footer">', "</footer>")

    snap, rows, dropped = load_reviews()
    testi = json.loads((DATA / "testimonials-snapshot.json").read_text(encoding="utf-8"))
    by_who = {clean_who(t["who"]): t for t in testi["home"]}
    stories = [by_who[w] for w in HOMEOWNERS]
    trade = testi["trade"]

    total = len(rows)
    five = sum(1 for r in rows if r["rating"] == 5)
    counts = {k: sum(1 for r in rows if r["key"] == k) for k in PRODUCTS}

    filters = ['<button type="button" class="chip is-on" data-filter="all" aria-pressed="true">'
               'All <span>%d</span></button>' % total]
    for k, (label, _) in PRODUCTS.items():
        filters.append('<button type="button" class="chip" data-filter="%s" aria-pressed="false">'
                       '%s <span>%d</span></button>' % (k, esc(label), counts[k]))

    page = TEMPLATE
    for key, val in {
        "@@TOKENS@@": tokens, "@@BASE@@": base, "@@HEADER_CSS@@": header_css,
        "@@FOOTER_CSS@@": footer_css, "@@HEADER@@": header, "@@FOOTER@@": footer,
        "@@TOTAL@@": "{:,}".format(total), "@@FIVE@@": "{:,}".format(five),
        "@@PULLED@@": snap["pulled"],
        "@@STORIES@@": "\n".join(story_card(t) for t in stories),
        "@@FILTERS@@": "\n".join(filters),
        "@@REVIEWS@@": "\n".join(review_card(r, i) for i, r in enumerate(rows)),
        "@@TRADE@@": "\n".join(trade_card(t) for t in trade),
        "@@PAGE_SIZE@@": str(PAGE_SIZE),
    }.items():
        page = page.replace(key, val)
    leftover = re.findall(r"@@[A-Z_]+@@", page)
    assert not leftover, leftover

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print("wrote", OUT.relative_to(ROOT), "%d bytes" % len(page.encode("utf-8")))
    print("reviews %d (5-star %d), duplicates dropped %d, per product %s" % (total, five, dropped, counts))
    print("no name %d, no location %d, no usable date %d, title only %d" % (
        sum(1 for r in rows if not r["name"]), sum(1 for r in rows if not r["location"]),
        sum(1 for r in rows if not r["date"]), sum(1 for r in rows if not r["paras"])))
    print("stories %d, trade testimonials %d" % (len(stories), len(trade)))


TEMPLATE = """<!DOCTYPE html>
<!--
  ============================================================================
  REVIEWS AND TESTIMONIALS, Modern House Numbers
  Proposed new page. There is no /pages/testimonials on the live site yet.
  GENERATED by build/build_testimonials.py from build/data/*.json. Do not edit
  this file by hand; change the script or the snapshots and re-run it.

  Reviews: the live site's own endpoint (cms.modernhousenumbers.com/reviews.php),
  snapshot of @@PULLED@@, wording untouched. Testimonials: the live homepage
  and live /pages/trade carousels. Header, footer and brand tokens are lifted
  from index.html.

  No Review or AggregateRating markup on purpose: star markup a business puts
  on reviews of itself is not eligible for rich results, and the product pages
  are where product review markup belongs.
  ============================================================================
-->
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Modern House Numbers Reviews | Customer Testimonials</title>
<meta name="description" content="Read @@TOTAL@@ customer reviews of Modern House Numbers, plus testimonials from architects, designers and builders who use our house numbers and plaques.">
<link rel="canonical" href="https://www.modernhousenumbers.com/pages/testimonials">
<meta name="robots" content="noindex,nofollow">
<!-- Preview deployment: noindex. The canonical is the proposed live URL,
     which does not exist yet. -->

<meta property="og:type" content="website">
<meta property="og:title" content="Modern House Numbers Reviews | Customer Testimonials">
<meta property="og:url" content="https://www.modernhousenumbers.com/pages/testimonials">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@200;300;400;500;600&family=Mulish:wght@300;400;600;700&display=swap">
<script>document.documentElement.className='js'</script>

<style>
/* ============ lifted from index.html ============ */
@@TOKENS@@
@@BASE@@
@@HEADER_CSS@@
@@FOOTER_CSS@@
.skip{position:absolute;left:-9999px}
.skip:focus{left:12px;top:12px;z-index:99;background:#fff;padding:.5rem .8rem;border:1px solid var(--ink)}

/* ============ this page ============ */
section[id],h2[id]{scroll-margin-top:92px}
.crumbs{font-size:.78rem;letter-spacing:.06em;color:var(--ink-soft);margin:0 0 18px}
.crumbs a{color:var(--ink-soft);text-decoration:underline;text-underline-offset:3px}
.crumbs a:hover{color:var(--orange)}
.crumbs span[aria-hidden]{margin:0 .45rem}

.rhero{background:var(--bg-soft);padding:30px 0 46px;border-bottom:1px solid var(--line-soft)}
.rhero h1{font-size:clamp(1.9rem,4.6vw,3rem);letter-spacing:0;text-transform:none;text-align:left;
  line-height:1.12;max-width:20ch;margin:0 0 .5em}
.rhero h1 b{font-weight:500}
.rhero-lead{max-width:62ch;margin:0 0 1.5rem}
.rhero-row{display:flex;flex-wrap:wrap;gap:14px;align-items:center}
.pill{display:inline-flex;flex-wrap:wrap;align-items:center;gap:.4rem .7rem;background:#fff;
  border:1px solid var(--line-soft);padding:.72rem 1.1rem;font-size:.9rem;line-height:1.3}
.pill b{font-weight:700}
.stars{color:var(--orange);letter-spacing:.1em;font-size:.95rem;line-height:1;white-space:nowrap}
.stars i{font-style:normal;color:#d5d4d4}

.sec-head{display:flex;flex-wrap:wrap;gap:8px 24px;align-items:flex-end;justify-content:space-between;margin-bottom:22px}
.sec-head h2{margin:0 0 .25em}
.sec-head p{margin:0;max-width:64ch;font-size:.95rem}

/* customer stories */
.stories{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
@media(max-width:960px){.stories{grid-template-columns:repeat(2,1fr)}}
@media(max-width:620px){.stories{grid-template-columns:1fr}}
.story{margin:0;border:1px solid var(--line-soft);background:#fff;display:flex;flex-direction:column}
.story img{width:100%;height:auto;aspect-ratio:700/320;object-fit:cover}
.story blockquote{margin:0;padding:18px 20px 0;flex:1}
.story-title{font-family:var(--head);font-weight:300;font-size:1.3rem;line-height:1.25;margin:0 0 .5rem}
.story blockquote p:last-child{font-size:.92rem;margin:0}
.story figcaption{padding:14px 20px 20px;font-weight:700;font-size:.86rem}

/* review cards */
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 22px}
.chip{font-family:var(--body);font-size:.78rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  background:#fff;color:var(--ink);border:1px solid var(--line);padding:.6rem .9rem;cursor:pointer;
  border-radius:0;line-height:1.2;min-height:40px}
.chip span{font-weight:400;color:var(--ink-soft);margin-left:.3rem;letter-spacing:.02em}
.chip:hover{border-color:var(--ink)}
.chip.is-on{background:var(--ink);border-color:var(--ink);color:#fff}
.chip.is-on span{color:#d9d7d4}
.chip:focus-visible,.btn:focus-visible{outline:2px solid var(--orange);outline-offset:2px}
.no-js .chips,.no-js .rv-more{display:none}

.rv-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
@media(max-width:760px){.rv-grid{grid-template-columns:1fr}}
.rv{margin:0;border:1px solid var(--line-soft);background:#fff;padding:20px 22px;display:flex;
  flex-direction:column;min-width:0}
.js .rv[hidden]{display:none}
.rv-top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}
.rv-src{font-size:.66rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);
  text-align:right}
.rv blockquote{margin:0;flex:1;overflow-wrap:anywhere}
.rv-title{font-weight:700;margin:0 0 .45rem}
.rv blockquote p{font-size:.92rem;margin:0 0 .7rem}
.rv figcaption{margin-top:10px;display:flex;flex-wrap:wrap;gap:2px 12px;align-items:baseline}
.rv-name{font-weight:700;font-size:.9rem}
.rv-meta{font-size:.78rem;color:var(--ink-soft)}
.rv-more{display:flex;flex-direction:column;align-items:center;gap:12px;margin-top:26px}
.rv-count{font-size:.82rem;color:var(--ink-soft);margin:0}

/* trade testimonials */
.trade-actions{display:flex;flex-wrap:wrap;gap:12px 18px;align-items:center;margin:0 0 24px}
.trade-actions a.link{text-decoration:underline;text-underline-offset:3px;font-weight:600}
.tts{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
@media(max-width:960px){.tts{grid-template-columns:repeat(2,1fr)}}
@media(max-width:620px){.tts{grid-template-columns:1fr}}
.tt{margin:0;background:var(--ink);color:#fff;display:flex;flex-direction:column}
.tt img{width:100%;height:auto;aspect-ratio:700/320;object-fit:cover}
.tt-body{padding:14px 22px 22px;display:flex;flex-direction:column;flex:1}
.tt-mark{font-family:Georgia,serif;font-size:2.6rem;line-height:1;color:var(--orange);height:1.9rem}
.tt blockquote{margin:0;flex:1}
.tt blockquote p{font-size:.95rem;margin:0 0 1.2rem}
.tt figcaption{font-weight:700;font-size:.88rem}
.tt-credit{font-size:.7rem;color:#b5b2ae;margin:.5rem 0 0}

/* closing band */
.band{background:var(--orange);color:#fff;padding:46px 0}
.band h2{color:#fff;font-weight:400;margin:0 0 .35em}
.band p{margin:0 0 1.3rem;max-width:60ch}
.band-actions{display:flex;flex-wrap:wrap;gap:12px}
.band .btn--dark{background:var(--ink);color:#fff}
.band .btn--dark:hover{background:#000}
.band .btn--line{background:transparent;color:#fff;border-color:#fff}
.band .btn--line:hover{background:#fff;color:var(--ink)}
@media(max-width:520px){.band .btn,.rhero-row .btn{width:100%}.container{padding:0 18px}}
</style>
</head>
<body>

<a class="skip" href="#main">Skip to content</a>

@@HEADER@@

<main id="main">

  <section class="rhero">
    <div class="container">
      <p class="crumbs"><a href="https://www.modernhousenumbers.com">Home</a><span aria-hidden="true">&rsaquo;</span>Reviews</p>
      <h1>Modern House Numbers Reviews: <b>Hear Directly from Our Customers</b></h1>
      <p class="rhero-lead">Homeowners, designers and builders share what it was like to order and install
        their Modern House Numbers. Every review on this page is shown as the customer wrote it.</p>
      <div class="rhero-row">
        <p class="pill" style="margin:0"><span class="stars" aria-hidden="true">&#9733;&#9733;&#9733;&#9733;&#9733;</span>
          <span><b>@@TOTAL@@</b> customer reviews</span><span>&middot;</span><span><b>@@FIVE@@</b> rated 5 stars</span></p>
        <a class="btn btn--primary" href="#reviews">Read the reviews</a>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="stories-h">
    <div class="container">
      <div class="sec-head">
        <div>
          <h2 id="stories-h">Customer Stories</h2>
          <p>Notes from homeowners about their new house numbers and plaques.</p>
        </div>
      </div>
      <div class="stories">
@@STORIES@@
      </div>
    </div>
  </section>

  <section class="section section--soft" id="reviews" aria-labelledby="reviews-h">
    <div class="container">
      <div class="sec-head">
        <div>
          <h2 id="reviews-h">Customer Reviews</h2>
          <p>Reviews left on our product pages, newest first. Choose a product to see only its reviews.</p>
        </div>
      </div>
      <div class="chips" role="group" aria-label="Filter reviews by product">
@@FILTERS@@
      </div>
      <div class="rv-grid" id="rv-grid">
@@REVIEWS@@
      </div>
      <div class="rv-more">
        <p class="rv-count" id="rv-count" aria-live="polite"></p>
        <button type="button" class="btn btn--ghost" id="rv-more-btn">Load more reviews</button>
      </div>
    </div>
  </section>

  <section class="section" aria-labelledby="trade-h">
    <div class="container">
      <div class="sec-head">
        <div>
          <h2 id="trade-h">Trade Testimonials from Architects, Designers and Builders</h2>
          <p>Design and building professionals on using Modern House Numbers in their projects.</p>
        </div>
      </div>
      <p class="trade-actions">
        <a class="btn btn--primary" href="https://www.modernhousenumbers.com/pages/trade">Explore the Trade Program</a>
        <a class="link" href="https://www.modernhousenumbers.com/pages/contact">or contact us</a>
      </p>
      <div class="tts">
@@TRADE@@
      </div>
    </div>
  </section>

  <section class="band" aria-labelledby="band-h">
    <div class="container">
      <h2 id="band-h">Ready to Order Your House Numbers?</h2>
      <p>Choose your font, finish and size, and we will make them to order.</p>
      <div class="band-actions">
        <a class="btn btn--dark" href="https://www.modernhousenumbers.com/products/house-numbers-letters">Shop Numbers + Letters</a>
        <a class="btn btn--line" href="https://www.modernhousenumbers.com/products/plaque">Shop Plaques</a>
        <a class="btn btn--line" href="https://www.modernhousenumbers.com/pages/contact">Contact Us</a>
      </div>
    </div>
  </section>

</main>

@@FOOTER@@

<script>
(function(){
  var PAGE=@@PAGE_SIZE@@, grid=document.getElementById('rv-grid');
  if(!grid) return;
  var cards=[].slice.call(grid.children), chips=[].slice.call(document.querySelectorAll('.chip')),
      btn=document.getElementById('rv-more-btn'), count=document.getElementById('rv-count'),
      filter='all', shown=PAGE;
  function render(){
    var match=0, visible=0;
    cards.forEach(function(c){
      var ok=filter==='all'||c.getAttribute('data-product')===filter;
      if(ok) match++;
      var show=ok&&match<=shown;
      c.hidden=!show; if(show) visible++;
    });
    count.textContent='Showing '+visible+' of '+match+' reviews';
    btn.hidden=visible>=match;
  }
  chips.forEach(function(ch){
    ch.addEventListener('click',function(){
      filter=ch.getAttribute('data-filter'); shown=PAGE;
      chips.forEach(function(o){var on=o===ch;o.classList.toggle('is-on',on);o.setAttribute('aria-pressed',on?'true':'false');});
      render();
    });
  });
  btn.addEventListener('click',function(){shown+=PAGE;render();});
  render();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
