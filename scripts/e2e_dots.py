"""Verify the dot distributions, the percentile ladder, and that nothing else broke."""
import pathlib, time, urllib.request
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:3150/"
OUT = pathlib.Path(__file__).resolve().parent.parent / "_shots"
OUT.mkdir(exist_ok=True)
TABS = ["overview", "structure", "wage", "demand", "pathways",
        "opportunity", "alignment", "regions", "about", "methods"]

for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

def open_section(pg, tab, label):
    """Click a tab, then the sub-section whose label starts with `label`."""
    pg.click(f"#tab-{tab}")
    pg.wait_for_timeout(420)
    btns = pg.locator(f"#view-{tab} .subnav button")
    for i in range(btns.count()):
        if btns.nth(i).inner_text().strip().lower().startswith(label.lower()):
            btns.nth(i).click()
            pg.wait_for_timeout(480)
            return True
    raise AssertionError(f"no section starting {label!r} on {tab}")

errs, perrs = [], []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 1500, "height": 1050})
    pg = ctx.new_page()
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: perrs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")

    print("--- every tab still renders ---")
    for t in TABS:
        pg.click(f"#tab-{t}")
        pg.wait_for_timeout(500)
        n = len(pg.locator(f"#view-{t}").inner_text())
        print(f"  {t:12s} {n:6d} {'OK' if n > 200 else 'EMPTY!'}")
        if n <= 200:
            errs.append(f"{t} empty")

    print("")
    print("--- no box plots left anywhere ---")
    for t in TABS:
        pg.click(f"#tab-{t}")
        pg.wait_for_timeout(350)
        txt = pg.locator(f"#view-{t}").inner_text().lower()
        for word in ("whisker", "the box the", "box plot"):
            if word in txt:
                errs.append(f"{t}: box-plot language left in copy ({word!r})")
                print(f"  {t}: STILL SAYS {word!r}")
    print("  checked all 8 tabs")

    def count(view, sel):
        return pg.locator(f"#view-{view} {sel}").count()

    print("")
    print("--- dot charts ---")
    for view, section, label in [
        ("structure", "Median pay", "families"),
        ("wage", "Median pay by size", "size bands"),
        ("wage", "Worker earnings", "people"),
        ("pathways", "What the job requires", "credential tiers"),
        ("pathways", "What people hold", "people"),
    ]:
        open_section(pg, view, section)
        dots = count(view, "svg circle.dot")
        over = count(view, "svg path.dot.over")
        cols = count(view, "svg .dotcol")
        rows = count(view, "svg .dotrow")
        print(f"  {view:10s} {section:24s} {label:16s} dots={dots:5d} "
              f"off-scale={over:4d} columns={cols} rows={rows}")
        if dots < 50:
            errs.append(f"{view}: only {dots} dots drawn")

    print("")
    print("--- percentile ladder (wage tab) ---")
    open_section(pg, "wage", "Mean against median")
    lad = pg.locator("#view-wage svg g.ladder")
    print(f"  ladder rows: {lad.count()}")
    meds = pg.locator("#view-wage svg g.ladder circle[stroke-width='1.2']").count()
    rings = pg.locator("#view-wage svg g.ladder circle[stroke-width='1.8']").count()
    print(f"  median dots: {meds}   mean rings: {rings}")
    if rings == 0:
        errs.append("ladder drew no mean markers")
    if lad.count() < 20:
        errs.append(f"ladder has only {lad.count()} rows")

    print("")
    print("--- hover a dot gives quick stats ---")
    open_section(pg, "pathways", "What the job requires")
    d = pg.locator("#view-pathways svg.dotcols circle.dot").nth(40)
    d.hover()
    pg.wait_for_timeout(350)
    tip = pg.locator("#tip")
    print(f"  tooltip visible: {tip.evaluate('e => getComputedStyle(e).opacity')}")
    print(f"  tooltip text: {tip.inner_text()[:150]!r}")
    if not tip.inner_text().strip():
        errs.append("dot hover produced no tooltip")

    print("")
    print("--- hover a person dot ---")
    open_section(pg, "pathways", "What people hold")
    pd = pg.locator("#view-pathways svg.dotcols circle.dot").nth(30)
    pd.hover()
    pg.wait_for_timeout(350)
    print(f"  tooltip text: {pg.locator('#tip').inner_text()[:150]!r}")

    print("")
    print("--- click a dot column opens the drill-down ---")
    open_section(pg, "pathways", "What the job requires")
    pg.locator("#view-pathways svg.dotcols .collabel.clickable").first.click()
    pg.wait_for_timeout(700)
    dr = pg.locator(".drill")
    print(f"  drill open: {dr.count() > 0}")
    if dr.count():
        print(f"  title: {dr.locator('h3').inner_text()!r}")
        print(f"  rows: {dr.locator('tbody tr').count()}")
        print(f"  has search + filter: "
              f"{dr.locator('.dtsearch').count() > 0 and dr.locator('.dtfilter select').count() > 0}")
    else:
        errs.append("clicking a dot column did not open the drill-down")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)

    for t, sec, name in [("structure", "Median pay", "families"),
                         ("wage", "Median pay by size", "wage"),
                         ("pathways", "What the job requires", "pathways")]:
        open_section(pg, t, sec)
        pg.screenshot(path=str(OUT / f"dots-{name}.png"), full_page=True)

    print("")
    print("--- mobile, 390px ---")
    pg.set_viewport_size({"width": 390, "height": 900})
    for t in TABS:
        pg.click(f"#tab-{t}")
        pg.wait_for_timeout(450)
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
