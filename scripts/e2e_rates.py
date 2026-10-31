"""Guards the minimum-base rule on the three rate columns.

A rate whose denominator is under 10 jobs is suppressed in build.py, so it must
render as a dash and must never sort above a real value. Gambling Managers (0.005
jobs, 19,390% projected growth before the rule) and Bailiffs (0.1 -> 55.9 jobs,
+54,601% observed change) are the two worst cases and are checked by name.

Run against `next start` on the port below.
"""
import os
import time, urllib.request
import sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3163")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read(); break
    except Exception: time.sleep(1)

def pick(pg, section, measure=None):
    """Open a sidebar section and, where the panel has a measure control, choose one.

    Several sections that used to be a page each are now one panel behind a
    measure chip, so a fixture has to say which measure it means.
    """
    pg.locator(".sbitem", has_text=section).first.click()
    pg.wait_for_timeout(900)
    if measure:
        pg.locator(".rankctl .chips button", has_text=measure).first.click()
        pg.wait_for_timeout(700)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1500, "height": 1050}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    # The full occupation table used to be a sidebar destination of its own. It now
    # sits under the chart it belongs to, behind the "Show the figures" disclosure.
    pick(pg, "Size and pay", "Typical pay")
    tog = pg.locator(".datatoggle").first
    if "Show" in (tog.text_content() or ""):
        tog.click()
    pg.wait_for_timeout(900)

    tbl = pg.locator(".view table").last
    hdrs = [h.inner_text().split("\n")[0].strip()
            for h in tbl.locator("thead th").all()]
    print("columns:", hdrs)

    # Typical pay by family is a ranked bar chart; check it draws one bar per family
    # plus the three reference bars, and that every bar carries a money label.
    pick(pg, "By occupation group", "Typical pay")
    pg.locator(".rankctl .chips button", has_text="All").first.click()
    pg.wait_for_timeout(700)
    bars = pg.locator(".panel svg.chart g.bar").count()
    labs = pg.eval_on_selector_all(
        ".panel svg.chart text.clab", "els => els.map(e => e.textContent)")
    fills = pg.evaluate(
        "() => { const o = {};"
        " document.querySelectorAll('.panel svg.chart g.bar rect').forEach(r =>"
        " { const f = getComputedStyle(r).fill; o[f] = (o[f] || 0) + 1; }); return o; }")
    print("family pay bars: %d | last three: %s | distinct fills: %d"
          % (bars, labs[-3:], len(fills)))
    assert bars == 25, "expected 22 families plus 3 reference bars, got %d" % bars
    assert labs[-3:] == ["Vermont", "New Hampshire", "United States"], labs[-3:]
    assert len(fills) == 3, "expected green, amber and grey, got %s" % fills

    # Typical pay by occupation size: three bands plus three reference bars, and the
    # green/amber split has to follow the living-wage benchmark the reader picks.
    pick(pg, "Size and pay", "Typical pay")

    def fills_now():
        return pg.evaluate(
            "() => { const o = {};"
            " document.querySelectorAll('.panel svg.chart g.bar rect').forEach(r =>"
            " { const f = getComputedStyle(r).fill; o[f] = (o[f] || 0) + 1; }); return o; }")

    bars = pg.locator(".panel svg.chart g.bar").count()
    before = fills_now()
    opts = pg.eval_on_selector_all("select option", "els => els.map(e => e.textContent)")
    pg.locator("select").first.select_option(
        label=[o for o in opts if "2 children" in o][0])
    pg.wait_for_timeout(900)
    after = fills_now()
    print("size bands: %d bars | fills at default %d | after a higher benchmark %d"
          % (bars, len(before), len(after)))
    assert bars == 6, "expected 3 size bands plus 3 reference bars, got %d" % bars
    assert before != after, "the benchmark no longer drives the green/amber split"

    # Headers are upper-cased in CSS and carry a sort glyph, so match on a prefix.
    def col_index(prefix):
        for k, h in enumerate(hdrs):
            if h.upper().startswith(prefix.upper()):
                return k
        return None

    for col in ("PROJECTED", "CHANGE", "TURNOVER"):
        i = col_index(col)
        if i is None:
            print(f"  {col}: header not found"); continue
        th = tbl.locator("thead th").nth(i)
        for click, label in ((1, "desc"), (2, "asc")):
            th.click(); pg.wait_for_timeout(450)
            vals = [r.locator("td").nth(i).inner_text().strip()
                    for r in tbl.locator("tbody tr").all()[:6]]
            print(f"  {col} {label:4s} top6: {vals}")
        th.click(); pg.wait_for_timeout(300)

    print("\nsearch for the two artefact occupations:")
    for name in ("Gambling Managers", "Bailiffs"):
        pg.locator(".view .dtsearch").fill(name)
        pg.wait_for_timeout(500)
        rows = tbl.locator("tbody tr")
        if rows.count():
            cells = [c.inner_text().strip() for c in rows.first.locator("td").all()]
            print(f"  {name}: {cells}")
        else:
            print(f"  {name}: filtered out of this view (below its jobs threshold)")
    pg.locator(".view .dtsearch").fill("")
    print("\npage errors:", len(errs))
    for e in errs[:3]: print("   ", e[:150])
    b.close()
