import sys, time, urllib.request, pathlib
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
URL = "http://127.0.0.1:3146/"
OUT = pathlib.Path(__file__).resolve().parent.parent / "_shots"
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read(); break
    except Exception: time.sleep(1)

def sec(pg, tab, label):
    pg.click(f"#tab-{tab}"); pg.wait_for_timeout(420)
    bs = pg.locator(f"#view-{tab} .subnav button")
    for i in range(bs.count()):
        if bs.nth(i).inner_text().strip().lower().startswith(label.lower()):
            bs.nth(i).click(); pg.wait_for_timeout(500); return
    raise AssertionError(label)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width":1400,"height":1000}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()"); pg.reload(wait_until="networkidle")

    for tab, label, name in [("structure","Industry sectors","silent (concentration)"),
                             ("structure","Median pay","comparator (vs nation)"),
                             ("wage","Wage quality by size","benchmark (living wage)"),
                             ("wage","Worker earnings","self (mean vs median)")]:
        sec(pg, tab, label)
        n = pg.locator(f"#view-{tab} .secbody .pnote")
        print(f"\n[{name}]  {label}")
        print("  " + (n.first.inner_text() if n.count() else "(no line — rule declined)"))

    print("\n--- does the benchmark line follow the living-wage selector? ---")
    sec(pg, "wage", "Wage quality by size")
    before = pg.locator("#view-wage .secbody .pnote").first.inner_text()
    opts = pg.locator("#view-wage select")
    vals = opts.first.evaluate("e => Array.from(e.options).map(o => o.value)")
    pg.select_option("#view-wage select", vals[-1]); pg.wait_for_timeout(700)
    after = pg.locator("#view-wage .secbody .pnote").first.inner_text()
    print(f"  {vals[0]}: {before[:95]}")
    print(f"  {vals[-1]}: {after[:95]}")
    print(f"  recomputed: {'YES' if before != after else 'NO — line is stale'}")
    pg.select_option("#view-wage select", vals[0]); pg.wait_for_timeout(500)

    sec(pg, "wage", "Wage quality by size")
    pg.locator("#view-wage .secbody .panel").first.screenshot(path=str(OUT/"insight.png"))
    print("\ninsight.png")
    print("page errors:", len(errs))
    b.close()
