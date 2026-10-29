"""The Employment tab's two new pieces: the industry drill-down and the age mix.

Checks that a sector bar opens the detailed industries beside it, that those rows
add up to the bar they came from, and that the age measure draws three ordered
bands per row whose shares reach 100%.

Run against a dev or `next start` server on VT_PORT.
"""
import os
import re
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

fails = []


def num(s):
    s = re.sub(r"[^0-9.]", "", s or "")
    return float(s) if s else 0.0


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1600, "height": 1100}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")

    # ---------------- industry drill-down ----------------
    print("--- a sector bar opens the industries inside it ---")
    pg.locator(".sbitem", has_text="Industry sectors").first.click()
    pg.wait_for_timeout(800)
    pg.locator(".rankctl .chips button", has_text="Share of jobs").first.click()
    pg.wait_for_timeout(600)

    bar = pg.locator(".split svg.chart g.bar").first
    name = (bar.get_attribute("aria-label") or "").strip()
    bar.click()
    pg.wait_for_timeout(500)

    pane = pg.locator(".detail")
    if not pane.count():
        fails.append("clicking a sector opened no pane")
    else:
        title = pane.locator("h4").inner_text().strip()
        rows = pane.locator(".minitable tbody tr").count()
        print("  %s -> %d industries listed" % (title, rows))
        if title != name:
            fails.append("clicked %r, pane says %r" % (name, title))
        if rows < 1:
            fails.append("pane listed no industries")
        if "industry" not in pane.locator(".minitable thead").inner_text().lower():
            fails.append("pane is not an industry table")

        # The pane's own headline has to match the bar it came from.
        head = pane.locator(".detail-stats .dv").first.inner_text()
        print("  headline jobs: %s" % head)
        if num(head) <= 0:
            fails.append("pane headline is not a job count")

    print("")
    print("--- and the full industry table is one click further on ---")
    more = pg.locator(".detail .morelink")
    if not more.count():
        fails.append("no way through to the full industry table")
    else:
        more.click()
        pg.wait_for_timeout(700)
        dr = pg.locator(".drill")
        if not dr.count():
            fails.append("the pane did not open the full industry table")
        else:
            hdrs = " / ".join(h.strip() for h in dr.locator("thead th").all_inner_texts())
            n = dr.locator("tbody tr").count()
            print("  drill rows: %d | columns: %s" % (n, hdrs))
            if "industry code" not in hdrs.lower():
                fails.append("full table is missing the industry code")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)

    # ---------------- age mix ----------------
    print("")
    print("--- the age measure draws three ordered bands ---")
    for section, hint in (("Industry sectors", "sector"), ("By type of work", "family")):
        pg.locator(".sbitem", has_text=section).first.click()
        pg.wait_for_timeout(700)
        pg.locator(".rankctl .chips button", has_text="Age mix").first.click()
        pg.wait_for_timeout(700)

        legend = [li.inner_text().strip() for li in pg.locator(".legend li").all()]
        want = ["Under 35", "35 to 54", "55 and over"]
        if legend != want:
            fails.append("%s: legend %r, wanted %r" % (hint, legend, want))

        svg = pg.locator(".split svg.chart").first
        rows = svg.locator("g.bar").count()
        groups = svg.locator("g > text.clab").count()
        print("  %-18s %d rows, %d segments" % (hint, groups, rows))
        if rows != groups * 3:
            fails.append("%s: %d segments over %d rows, expected 3 each"
                         % (hint, rows, groups))

        # Every row's segments have to fill the plot: a 100% stack that does not
        # reach 100% is a row with a band silently dropped.
        widths = pg.evaluate(
            """() => {
              const svg = document.querySelector('.split svg.chart');
              const by = {};
              svg.querySelectorAll('g.bar rect').forEach(r => {
                const y = r.getAttribute('y');
                by[y] = (by[y] || 0) + parseFloat(r.getAttribute('width'));
              });
              return Object.values(by);
            }"""
        )
        if widths:
            lo, hi = min(widths), max(widths)
            print("  %-18s stack widths %.0f to %.0f" % (hint, lo, hi))
            if hi - lo > 8:
                fails.append("%s: stacks differ by %.0f, so they are not 100%%"
                             % (hint, hi - lo))

        # The right-hand figure is the 55+ share, and the rows are sorted by it.
        rights = pg.eval_on_selector_all(
            ".split svg.chart text.vlab", "els => els.map(e => e.textContent)")
        vals = [num(t) for t in rights]
        print("  %-18s 55+ runs %s ... %s" % (hint, rights[0], rights[-1]))
        if vals != sorted(vals, reverse=True):
            fails.append("%s: rows are not ordered by the 55+ share" % hint)

        # Clicking a stacked row opens the same pane the bars do.
        svg.locator("g.bar").first.click()
        pg.wait_for_timeout(500)
        if not pg.locator(".detail").count():
            fails.append("%s: a stacked row does not open the detail" % hint)
        else:
            pg.locator(".detail .dxclose").click()
            pg.wait_for_timeout(300)

    b.close()

if errs:
    print("PAGE ERRORS:", errs)
print("")
print("FAIL: " + "; ".join(fails) if fails else "CLEAN")
sys.exit(1 if fails or errs else 0)
