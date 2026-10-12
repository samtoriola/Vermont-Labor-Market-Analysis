"""Every panel holding a chart should carry the figures behind it.

Walks each section and reports panels that draw a chart but offer no table, and
tables that come back empty when opened.
"""
import os
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3163")

missing, empty, ok = [], [], 0
perrs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1700, "height": 1000})
    pg.on("pageerror", lambda e: perrs.append(str(e)))
    pg.goto(URL)
    pg.wait_for_timeout(1800)

    labels = pg.eval_on_selector_all(".sbitem", "els => els.map(e => e.textContent)")
    for lab in labels:
        pg.locator(".sbitem", has_text=lab).first.click()
        pg.wait_for_timeout(700)
        panels = pg.evaluate(
            """() => [...document.querySelectorAll('.panel')].map(p => ({
                 title: (p.querySelector('h3') || {}).textContent || '?',
                 chart: !!p.querySelector('svg.chart'),
                 data: !!p.querySelector('.paneldata'),
               }))"""
        )
        for pn in panels:
            if not pn["chart"]:
                continue
            if not pn["data"]:
                missing.append((lab.strip(), pn["title"][:52]))
            else:
                ok += 1

        # open every table on this section and check it has rows
        togs = pg.locator(".datatoggle")
        for i in range(togs.count()):
            t = togs.nth(i)
            if "Show" in (t.text_content() or ""):
                t.click()
                pg.wait_for_timeout(350)
        n = pg.locator(".paneldata .datatable tbody tr").count()
        if pg.locator(".paneldata").count() and n == 0:
            empty.append(lab.strip())

    b.close()

print("charts with a table: %d" % ok)
if missing:
    print("charts with NO table (%d):" % len(missing))
    for s, t in missing:
        print("   %-24s %s" % (s, t))
if empty:
    print("sections where a table opened empty: %s" % ", ".join(empty))
print("page errors: %d" % len(perrs))
for e in perrs[:4]:
    print("  ", e[:170])

raise SystemExit(1 if (empty or perrs) else 0)
