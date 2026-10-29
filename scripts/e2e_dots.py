"""Verify the charts that plot many marks, and that nothing else broke.

Named for the dot columns it was written against. Those are all bar charts now, so
it asserts none has crept back, and covers what still plots per-occupation marks:
the percentile ladder and the size-against-pay scatter.
"""
import os
import pathlib, time, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3163")
OUT = pathlib.Path(__file__).resolve().parent.parent / "_shots"
OUT.mkdir(exist_ok=True)

for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

def open_section(pg, tab, label):
    """Click the sidebar entry whose label starts with `label`.

    `tab` is kept only to name the destination in failures: the sidebar lists every
    section directly, so there is no tab to open first.
    """
    items = pg.locator(".sbitem")
    for i in range(items.count()):
        if items.nth(i).inner_text().strip().lower().startswith(label.lower()):
            items.nth(i).click()
            pg.wait_for_timeout(480)
            return True
    raise AssertionError(f"no sidebar entry starting {label!r} (for {tab})")

errs, perrs = [], []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 1500, "height": 1050})
    pg = ctx.new_page()
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: perrs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")

    print("--- every sidebar destination renders ---")
    items = pg.locator(".sbitem")
    for i in range(items.count()):
        lab = items.nth(i).inner_text().strip()
        items.nth(i).click()
        pg.wait_for_timeout(380)
        n = len(pg.locator(".view").inner_text())
        print(f"  {lab:30s} {n:6d} {'OK' if n > 150 else 'EMPTY!'}")
        if n <= 150:
            errs.append(f"{lab} empty")

    print("")
    print("--- no box plots left anywhere ---")
    for i in range(items.count()):
        t = items.nth(i).inner_text().strip()
        items.nth(i).click()
        pg.wait_for_timeout(330)
        txt = pg.locator(".view").inner_text().lower()
        for word in ("whisker", "the box the", "box plot"):
            if word in txt:
                errs.append(f"{t}: box-plot language left in copy ({word!r})")
                print(f"  {t}: STILL SAYS {word!r}")
    print("  checked every destination")

    def count(view, sel):
        return pg.locator(f".view {sel}").count()

    print("")
    print("--- no dot columns are left ---")
    # Every occupation and person chart is a bar chart now. The dot components still
    # exist in components/dots.js, so this asserts none of them has crept back onto
    # a page rather than that they are gone from the codebase.
    stray = []
    for i in range(items.count()):
        items.nth(i).click()
        pg.wait_for_timeout(260)
        if pg.locator(".view svg.dotcols, .view svg .dotrow").count():
            stray.append(items.nth(i).inner_text().strip())
    print(f"  sections still drawing dot columns: {stray or 'none'}")
    if stray:
        errs.append(f"dot columns reappeared on {stray}")

    print("")
    print("--- percentile ladder (wage tab) ---")
    open_section(pg, "wage", "Mean against median")
    lad = pg.locator(".view svg g.ladder")
    print(f"  ladder rows: {lad.count()}")
    meds = pg.locator(".view svg g.ladder circle[stroke-width='1.2']").count()
    rings = pg.locator(".view svg g.ladder circle[stroke-width='1.8']").count()
    print(f"  median dots: {meds}   mean rings: {rings}")
    if rings == 0:
        errs.append("ladder drew no mean markers")
    if lad.count() < 20:
        errs.append(f"ladder has only {lad.count()} rows")

    print("")
    print("--- scatter still plots every occupation ---")
    open_section(pg, "wage", "Size against pay")
    pts = pg.locator(".view svg circle").count()
    print(f"  points: {pts}")
    if pts < 200:
        errs.append(f"scatter drew only {pts} points")

    print("")
    print("--- hover a bar gives quick stats ---")
    open_section(pg, "pathways", "By credential level")
    # The spread the dot columns used to show now lives on the pay measure's
    # hover, and this panel opens on the employment-share measure.
    pg.locator(".rankctl .chips button", has_text="Typical pay").first.click()
    pg.wait_for_timeout(600)
    pg.locator(".view svg.chart g.bar").nth(3).hover()
    pg.wait_for_timeout(350)
    tip = pg.locator("#tip")
    print(f"  tooltip visible: {tip.evaluate('e => getComputedStyle(e).opacity')}")
    print(f"  tooltip text: {tip.inner_text()[:150]!r}")
    if not tip.inner_text().strip():
        errs.append("bar hover produced no tooltip")

    print("")
    print("--- the range is still reachable on a bar ---")
    txt = tip.inner_text()
    for want in ("Middle half pays", "Lowest-paid tenth", "Highest-paid tenth"):
        if want not in txt:
            errs.append(f"bar hover lost {want!r}")
    print(f"  carries the spread: {all(w in txt for w in ('Middle half pays', 'Lowest-paid tenth'))}")

    print("")
    print("--- clicking a bar opens the detail beside it ---")
    open_section(pg, "pathways", "By credential level")
    pg.locator(".view svg.chart g.bar").first.click()
    pg.wait_for_timeout(700)
    pane = pg.locator(".detail")
    print(f"  pane open: {pane.count() > 0}")
    if pane.count():
        print(f"  title: {pane.locator('h4').inner_text()!r}")
        print(f"  occupations shown: {pane.locator('.minitable tbody tr').count()}")
    else:
        errs.append("clicking a bar did not open the detail pane")

    print("")
    print("--- and the whole table is still one click further on ---")
    more = pg.locator(".detail .morelink")
    if not more.count():
        errs.append("detail pane has no way through to the full table")
    else:
        more.click()
        pg.wait_for_timeout(700)
        dr = pg.locator(".drill")
        print(f"  drill open: {dr.count() > 0}")
        if dr.count():
            print(f"  title: {dr.locator('h3').inner_text()!r}")
            print(f"  rows: {dr.locator('tbody tr').count()}")
            print(f"  has search + filter: "
                  f"{dr.locator('.dtsearch').count() > 0 and dr.locator('.dtfilter select').count() > 0}")
        else:
            errs.append("the detail pane did not open the full table")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)

    for t, sec, name in [("wage", "Mean against median", "ladder"),
                         ("wage", "Size against pay", "scatter")]:
        open_section(pg, t, sec)
        pg.screenshot(path=str(OUT / f"dots-{name}.png"), full_page=True)

    print("")
    print("--- mobile, 390px ---")
    pg.set_viewport_size({"width": 390, "height": 900})
    for i in range(items.count()):
        t = items.nth(i).inner_text().strip()
        items.nth(i).click()
        pg.wait_for_timeout(330)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        cw = pg.evaluate("document.documentElement.clientWidth")
        if sw > cw + 1:
            errs.append(f"{t}: h-scroll +{sw-cw}px")
            print(f"  {t}: H-SCROLL +{sw-cw}px")
    print("  checked")
    b.close()

print("")
print("console errors:", len(errs), "| page errors:", len(perrs))
for e in (errs + perrs)[:10]:
    print("   ", e[:170])
print("")
print("RESULT:", "CLEAN" if not (errs or perrs) else "ISSUES")
