"""Vendor and survey names belong on About and Methods, nowhere else.

The charts name what the data is and when it is from; who publishes it is stated
once, in general terms, on the two reference tabs. Nothing else in the toolchain
would notice a name creeping back into a caption or a source line.
"""
import os
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3163")
NAMES = ["Lightcast", "CPS", "IPUMS", "OEWS", "IPEDS", "NAICS", "SOC ",
         "American Community Survey", "TIGER", "MIT Living Wage", "cip2020", "MAJORNUM"]
ALLOWED = {"About", "Methods"}

hits = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1700, "height": 1000})
    pg.goto(URL)
    pg.wait_for_timeout(1800)

    labels = pg.eval_on_selector_all(".sbitem", "els => els.map(e => e.textContent)")
    for lab in labels:
        if lab.strip() in ALLOWED:
            continue
        pg.locator(".sbitem", has_text=lab).first.click()
        pg.wait_for_timeout(600)
        # open the tables too -- their column headers are reader-facing
        togs = pg.locator(".datatoggle")
        for i in range(togs.count()):
            t = togs.nth(i)
            if "Show" in (t.text_content() or ""):
                t.click()
                pg.wait_for_timeout(250)
        txt = pg.evaluate("() => document.querySelector('.view').innerText")
        for n in NAMES:
            if n in txt:
                hits.append((lab.strip(), n))
    b.close()

if hits:
    print("source names outside About and Methods (%d):" % len(hits))
    for s, n in hits:
        print("   %-26s %s" % (s, n))
else:
    print("No source names outside About and Methods.")

raise SystemExit(1 if hits else 0)
