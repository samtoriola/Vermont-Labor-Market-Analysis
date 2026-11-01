"""Chart and detail side by side.

Checks the whole interaction on every panel that has it: the chart starts full
width with no pane and no faded bars, a click opens the pane for that bar and
fades the rest, a second click on the same bar closes it again, and the figures
in the pane are the ones the chart was drawn from.

Also checks the hover card carries its headline number and its click hint.

Run against a dev or `next start` server on VT_PORT.
"""
import os
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

# (sidebar section, measure chip or None, which bar to click)
#
# Several of these used to be a section each and are now one panel behind a
# measure control, so the pane has to work on every measure, not just the one the
# panel opens on.
PANELS = [
    ("Occupation", "Share of jobs", 0),
    ("Occupation", "Typical pay", 0),
    ("By credential level", "Share of jobs", 0),
    # Typical pay, Above living wage and Range of outcomes were three chips over
    # one distribution. The pay ladder replaced all three, and e2e_pathways.py
    # checks it against the arithmetic; here it only has to open a pane.
    ("By credential level", "The pay ladder", 0),
    ("Against demand", "By occupation group", 0),
]


# How many rows read as dimmed on screen, counted on the row LABEL rather than on
# the mark. Three charts fade three different things: a plain ranked bar fades its
# own fill, a range row fades the group around it, and a chart whose colour is a
# measure -- an absent pipeline, a credential's four ranks -- holds its fill at
# full strength and fades only the label, because washing those colours together
# is what the fade would destroy. The label is the one part every chart fades, and
# there is exactly one per row.
DIMMED_JS = """() => [...document.querySelectorAll('.split svg.chart text.clab')]
  .filter(t => {
    for (let el = t; el && el.tagName !== 'svg'; el = el.parentElement) {
      if (parseFloat(getComputedStyle(el).opacity) < 0.99) return true;
    }
    return false;
  }).length"""


def dimmed(pg):
    return pg.evaluate(DIMMED_JS)


fails = []

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1600, "height": 1100}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")

    for section, measure, idx in PANELS:
        label = section if not measure else "%s / %s" % (section, measure)
        pg.locator(".sbitem", has_text=section).first.click()
        pg.wait_for_timeout(700)
        if measure:
            pg.locator(".rankctl .chips button", has_text=measure).first.click()
            pg.wait_for_timeout(600)

        split = pg.locator(".split").first
        if split.count() == 0:
            fails.append("%s: no .split" % label)
            continue

        # Closed to begin with.
        if pg.locator(".detail").count():
            fails.append("%s: pane open before any click" % label)
        if "open" in (split.get_attribute("class") or ""):
            fails.append("%s: split marked open before any click" % label)
        faded = dimmed(pg)
        if faded:
            fails.append("%s: %d rows faded with nothing chosen" % (label, faded))

        bars = pg.locator(".split svg.chart g.bar")
        n_before = bars.count()
        bar = bars.nth(idx)
        name = (bar.get_attribute("aria-label") or "").strip()

        bar.click()
        pg.wait_for_timeout(500)

        pane = pg.locator(".detail")
        if pane.count() != 1:
            fails.append("%s: click opened %d panes" % (label, pane.count()))
            continue
        title = pane.locator("h4").inner_text().strip()
        if title != name:
            fails.append("%s: clicked %r, pane says %r" % (label, name, title))
        if not pane.locator(".minitable tbody tr").count():
            fails.append("%s: pane has no occupations" % label)
        if not pane.locator(".detail-stats .dv").count():
            fails.append("%s: pane has no headline figures" % label)

        # Every row but the chosen one fades. Reference bars fade with the rest,
        # so the count is "all but one" rather than a number worth naming here.
        faded = dimmed(pg)
        if faded != n_before - 1:
            fails.append(
                "%s: %d of %d rows faded, expected %d"
                % (label, faded, n_before, n_before - 1)
            )

        # The chart kept every bar; only its coordinate width changed.
        if bars.count() != n_before:
            fails.append("%s: bars went %d -> %d" % (label, n_before, bars.count()))
        vb = pg.locator(".split svg.chart").first.get_attribute("viewBox")
        if not vb.startswith("0 0 1040"):
            fails.append("%s: chart did not narrow (viewBox %s)" % (label, vb))

        # Clicking the same bar again puts the width back.
        bars.nth(idx).click()
        pg.wait_for_timeout(400)
        if pg.locator(".detail").count():
            fails.append("%s: second click did not close the pane" % label)
        vb = pg.locator(".split svg.chart").first.get_attribute("viewBox")
        if not vb.startswith("0 0 1180"):
            fails.append("%s: chart did not widen back (viewBox %s)" % (label, vb))

        print("%-42s ok  (%s)" % (label, name))

    # The hover card: a headline number, and the hint that a click does something.
    pg.locator(".sbitem", has_text="Occupation").first.click()
    pg.wait_for_timeout(600)
    pg.locator(".split svg.chart g.bar").first.hover()
    pg.wait_for_timeout(300)
    tip = pg.locator("#tip")
    if not tip.locator(".tbig .bv").count():
        fails.append("tooltip: no headline value")
    if not tip.locator(".tfoot").count():
        fails.append("tooltip: no click hint on a clickable bar")
    print("tooltip:", tip.inner_text().replace("\n", " | "))

    b.close()

if errs:
    print("PAGE ERRORS:", errs)
print("FAIL: " + "; ".join(fails) if fails else "CLEAN")
sys.exit(1 if fails or errs else 0)
