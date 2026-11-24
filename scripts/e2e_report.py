"""The Report tab: the output agrees with the tabs it came from.

A report travels away from the dashboard, so the thing that matters is not that
it renders but that it cannot print a figure the tool would contradict. Two of
these checks exist because the first build did exactly that:

  openings a year   48,718 printed against the home page's 48,893, because
                    summing the 22 occupation groups drops the occupations that
                    carry no group
  share below       42.5% printed against Wage quality's 41.1%, because rolling
                    the five credential tiers up is not the same arithmetic as
                    reading every occupation's pay ladder

Both are recomputed here from data/ and compared with what the page prints.

Also checked: every scope builds (all 14 counties, all 22 groups, a sample of
programs), both formats render, the benchmark moves the figures, the caveats
reach the output, and the rendered text carries none of the words
check_report_language.py bans -- that check reads the source, this one reads
what a person would actually see, which includes anything arriving from data.

Run against a dev or `next start` server on VT_PORT.
"""
import json
import os
import re
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(open(os.path.join(HERE, "..", "data", n), encoding="utf-8"))
LC = D("lightcast.json")
PCT = D("percentiles.json")
SOW = D("sow.json")
CTY = D("counties.json")

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []

# ---- the arithmetic the page has to match, computed here independently -----

PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]


def share_below(box, floor):
    if not box:
        return None
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    if len(xs) < 2:
        return None
    if floor <= xs[0][0]:
        return 0.0
    if floor >= xs[-1][0]:
        return 100.0
    for i in range(len(xs) - 1):
        v0, q0 = xs[i]
        v1, q1 = xs[i + 1]
        if v0 <= floor <= v1:
            t = 0 if v1 == v0 else (floor - v0) / (v1 - v0)
            return q0 + t * (q1 - q0)
    return None


def state_below(lw_key):
    floor = LC["livingWage"][lw_key] * LC["hours"]
    tot = 0.0
    bel = 0.0
    for o in LC["allOcc"]:
        s = share_below(PCT["occ"].get(o.get("s")), floor)
        if s is None:
            continue
        j = o.get("j") or 0.0
        tot += j
        bel += j * s / 100
    return 100 * bel / tot if tot else None


OPEN = LC["openTotal"] / LC["openYears"]
ADDED = sum((o.get("g5") or 0) for o in LC["allOcc"]) / 5
BELOW_DEFAULT = state_below(LC["defaultLW"])

print("expected: openings %s/yr, added %s/yr, below %.1f%%"
      % ("{:,.0f}".format(OPEN), "{:,.0f}".format(ADDED), BELOW_DEFAULT))

# Words the output must not contain, mirroring check_report_language.py.
BANNED = ["best", "worst", "poor", "problem", "crisis", "failing", "underpaid",
          "healthy", "struggling", "alarming", "troubling", "should", "must",
          "simply", "clearly", "obviously", "vulnerable", "mismatch"]


def chips(pg, group):
    return pg.locator(".rankctl", has_text=group).locator("button")


def pick_chip(pg, group, label):
    chips(pg, group).filter(has_text=re.compile("^%s$" % re.escape(label))).first.click()
    pg.wait_for_timeout(700)


def out_text(pg):
    return " ".join(pg.locator("#rpt-out").inner_text().split())


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1400}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(600)
    pg.locator(".sbitem", has_text="Report").first.click()
    pg.wait_for_timeout(1400)

    if not pg.locator("#rpt-out").count():
        fails.append("the report output did not render at all")
        print("FAIL  no #rpt-out")
        b.close()
        sys.exit(1)

    # ---- 1. the two figures that disagreed with the tabs on the first build
    txt = out_text(pg)
    want_open = "{:,.0f}".format(OPEN)
    want_below = "%.1f%%" % BELOW_DEFAULT
    print("\n--- Vermont / one-pager ---")
    print("  openings printed as %s (home page prints %s)"
          % ("found" if want_open in txt else "MISSING", want_open))
    if want_open not in txt:
        fails.append("openings a year: %s is not in the output (the home page prints it)" % want_open)
    if want_below not in txt:
        fails.append("share below: %s is not in the output (Wage quality prints it)" % want_below)
    else:
        print("  share below printed as %s, matching Wage quality" % want_below)

    # The number of findings should match what the control bar claims.
    n_fnd = pg.locator("#rpt-out .rfnd").count()
    claim = pg.locator(".rptgo .ctrlnote").inner_text()
    m = re.search(r"(\d+) findings", claim)
    if not m or int(m.group(1)) != n_fnd:
        fails.append("control bar says %r but the page has %d findings" % (claim, n_fnd))
    print("  %d findings rendered, control bar agrees" % n_fnd)

    # Every finding needs a figure the reader can check, not just a headline.
    thin = []
    for i in range(n_fnd):
        f = pg.locator("#rpt-out .rfnd").nth(i)
        has = f.locator(".rbar").count() + f.locator(".rtbl tr").count() + f.locator(".rstat").count()
        if not has:
            thin.append(f.locator("h4").inner_text()[:50])
        if not f.locator(".rsrc").count():
            fails.append("a finding carries no source line: %s" % f.locator("h4").inner_text()[:50])
    if thin:
        fails.append("findings with no figures under them: %s" % thin)

    # Caveats travel with the output.
    for key in ["jobs, not people", "modelled", "pay distribution"]:
        if key.lower() not in txt.lower():
            fails.append("the one-pager does not carry the caveat about %r" % key)

    # ---- 2. the benchmark actually moves the figures
    sel = pg.locator("#lw-select")
    sel.select_option(value="1 adult, 1 child")
    pg.wait_for_timeout(900)
    txt2 = out_text(pg)
    want2 = "%.1f%%" % state_below("1 adult, 1 child")
    if want2 not in txt2:
        fails.append("after switching benchmark, %s is not in the output" % want2)
    else:
        print("  benchmark switch moves the share to %s" % want2)
    if txt2 == txt:
        fails.append("switching the benchmark changed nothing in the output")
    sel.select_option(value=LC["defaultLW"])
    pg.wait_for_timeout(800)

    # ---- 3. the deck renders, and prints every slide rather than one
    pick_chip(pg, "Format", "Slide deck")
    n_sl = pg.locator("#rpt-out .rslide").count()
    shown = pg.locator("#rpt-out .rslide:not(.off)").count()
    print("\n--- Vermont / slide deck ---")
    print("  %d slides in the DOM, %d visible" % (n_sl, shown))
    if n_sl != n_fnd + 2:
        fails.append("%d slides for %d findings; expected %d" % (n_sl, n_fnd, n_fnd + 2))
    if shown != 1:
        fails.append("%d slides visible at once; the viewer should show one" % shown)
    # All of them have to be in the document, or printing yields a one-slide deck.
    if n_sl < 3:
        fails.append("the deck has fewer than three slides")
    pg.locator(".rdots .rdot").nth(2).click()
    pg.wait_for_timeout(500)
    if pg.locator("#rpt-out .rslide:not(.off)").count() != 1:
        fails.append("after paging, the deck does not show exactly one slide")

    # ---- 3b. no slide silently drops a row ----------------------------
    # The frame is fixed 16:9 and clips rather than scrolls, so content that
    # does not fit simply disappears -- at its worst a source line reading
    # "five highest replacement rates, and the lowest" sat above four rows.
    # Measured with rectangles, not scrollHeight: the fit box is scaled with a
    # transform, which layout metrics do not see.
    CLIP = """() => {
      const s = document.querySelector('.rslide:not(.off)');
      const bdy = s.querySelector('.rbody');
      if (!bdy) return { over: 0, head: '' };
      const inner = bdy.firstElementChild;
      const br = bdy.getBoundingClientRect();
      let bottom = br.top;
      Array.from(inner ? inner.children : []).forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.height) bottom = Math.max(bottom, r.bottom);
      });
      return { over: Math.round(bottom - br.bottom),
               head: s.querySelector('h3').textContent.slice(0, 44) };
    }"""

    def clip_scan(tag):
        n = pg.locator(".rdots .rdot").count()
        worst = []
        for i in range(n):
            pg.locator(".rdots .rdot").nth(i).click()
            pg.wait_for_timeout(190)
            o = pg.evaluate(CLIP)
            # Up to 6px is the last row's own border, not a dropped row.
            if o["over"] > 6:
                worst.append((i + 1, o["over"], o["head"]))
        print("  %-22s %d slides, clipped: %s" % (tag, n, worst or "none"))
        if worst:
            fails.append("%s: slides clip their content: %s" % (tag, worst))
        return n

    print()
    pick_chip(pg, "Format", "Slide deck")
    clip_scan("Vermont")

    # ---- 4. every scope builds
    print("\n--- every scope ---")
    for group, label, sel_id, n_expect in [
        ("Scope", "A county", "#rpt-pick", 14),
        ("Scope", "An occupation group", "#rpt-pick", 22),
        ("Scope", "A VSCS program", "#rpt-pick", None),
    ]:
        pick_chip(pg, group, label)
        pick_chip(pg, "Format", "One-pager")
        opts = pg.locator(sel_id + " option")
        n = opts.count()
        if n_expect and n != n_expect:
            fails.append("%s offers %d options, expected %d" % (label, n, n_expect))
        print("  %-22s %d options" % (label, n))
        # Walk a sample rather than all 149 programs: first, middle, last.
        idx = sorted({0, n // 2, n - 1})
        for i in idx:
            val = opts.nth(i).get_attribute("value")
            pg.locator(sel_id).select_option(value=val)
            pg.wait_for_timeout(450)
            k = pg.locator("#rpt-out .rfnd").count()
            t = out_text(pg)
            if k == 0:
                fails.append("%s = %r produced no findings" % (label, val))
            if "NaN" in t or "undefined" in t or "—%" in t:
                fails.append("%s = %r prints a broken figure" % (label, val))
            bad = [w for w in BANNED if re.search(r"(?<![a-z])%s(?![a-z])" % w, t.lower())]
            if bad:
                fails.append("%s = %r prints a word that grades: %s" % (label, val, bad))
        print("    sampled %d of them, all built" % len(idx))
        # The deck for this scope, on the option left selected above.
        pick_chip(pg, "Format", "Slide deck")
        clip_scan(label)
        pick_chip(pg, "Format", "One-pager")

    # ---- 4b. the one-pager is one page -------------------------------
    # The name is a promise, and it is the promise that breaks quietly: adding
    # a finding, or a county whose name wraps a headline, costs a line and the
    # document silently becomes two pages. Counted from a real PDF rather than
    # from element heights, because the panel's own chrome printing above the
    # report is what made it five pages the first time and no element
    # measurement of the report itself would have shown that.
    print()
    pick_chip(pg, "Format", "One-pager")
    for label in ["Vermont", "A county", "An occupation group", "A VSCS program"]:
        pick_chip(pg, "Scope", label)
        pdf = pg.pdf(format="Letter", print_background=True,
                     margin={"top": "0.5in", "bottom": "0.5in",
                             "left": "0.5in", "right": "0.5in"})
        n = len(re.findall(rb"/Type\s*/Page[^s]", pdf))
        print("  one-pager / %-22s %d page(s)" % (label, n))
        if n != 1:
            fails.append("the one-pager prints %d pages for %s" % (n, label))

    # The deck is the opposite promise: every slide on its own page, not just
    # the one the viewer happens to be showing.
    pick_chip(pg, "Scope", "Vermont")
    pick_chip(pg, "Format", "Slide deck")
    want = pg.locator("#rpt-out .rslide").count()
    pdf = pg.pdf(format="Letter", print_background=True,
                 margin={"top": "0.5in", "bottom": "0.5in",
                         "left": "0.5in", "right": "0.5in"})
    n = len(re.findall(rb"/Type\s*/Page[^s]", pdf))
    print("  deck / Vermont             %d page(s) for %d slides" % (n, want))
    if n != want:
        fails.append("the deck prints %d pages for %d slides" % (n, want))
    pick_chip(pg, "Format", "One-pager")

    # ---- 5. back to Vermont, and the rendered text stays clean
    pick_chip(pg, "Scope", "Vermont")
    t = out_text(pg)
    bad = [w for w in BANNED if re.search(r"(?<![a-z])%s(?![a-z])" % w, t.lower())]
    if bad:
        fails.append("the Vermont report prints a word that grades: %s" % bad)
    else:
        print("\n  rendered text carries none of the %d banned terms" % len(BANNED))

    if errs:
        fails.append("page errors: %s" % errs[:2])
    b.close()

print()
if fails:
    for f in fails:
        print("FAIL  %s" % f)
    sys.exit(1)
print("OK  the report agrees with the tabs it came from")
