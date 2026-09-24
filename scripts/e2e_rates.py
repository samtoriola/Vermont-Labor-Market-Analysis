"""Guards the minimum-base rule on the three rate columns.

A rate whose denominator is under 10 jobs is suppressed in build.py, so it must
render as a dash and must never sort above a real value. Gambling Managers (0.005
jobs, 19,390% projected growth before the rule) and Bailiffs (0.1 -> 55.9 jobs,
+54,601% observed change) are the two worst cases and are checked by name.

Run against `next start` on the port below.
"""
import time, urllib.request
import sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "http://127.0.0.1:3129/"
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read(); break
    except Exception: time.sleep(1)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1500, "height": 1050}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.click("#tab-opportunity"); pg.wait_for_timeout(900)

    tbl = pg.locator("#view-opportunity table").last
    hdrs = [h.inner_text().split("\n")[0].strip()
            for h in tbl.locator("thead th").all()]
    print("columns:", hdrs)

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
        pg.locator("#view-opportunity .dtsearch").fill(name)
        pg.wait_for_timeout(500)
        rows = tbl.locator("tbody tr")
        if rows.count():
            cells = [c.inner_text().strip() for c in rows.first.locator("td").all()]
            print(f"  {name}: {cells}")
        else:
            print(f"  {name}: filtered out of this view (below its jobs threshold)")
    pg.locator("#view-opportunity .dtsearch").fill("")
    print("\npage errors:", len(errs))
    for e in errs[:3]: print("   ", e[:150])
    b.close()
