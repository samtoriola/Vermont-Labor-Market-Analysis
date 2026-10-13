"""No commented-out block should render as text.

In JSX a `//` line is content, not a comment: it renders. Sections hidden inside
a JS array literal are fine, panels hidden in JSX markup are not, and the two
look identical in a diff. This walks every section and fails if any marker from
a hidden block reached the page.
"""
import os
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3163")
MARKERS = ["Hidden for now", "Restore by", "<Panel", "className=", "render: ()", "/*", "*/"]

hits = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1700, "height": 1000})
    pg.goto(URL)
    pg.wait_for_timeout(1800)

    labels = pg.eval_on_selector_all(".sbitem", "els => els.map(e => e.textContent)")
    for lab in labels:
        pg.locator(".sbitem", has_text=lab).first.click()
        pg.wait_for_timeout(600)
        txt = pg.evaluate("() => document.querySelector('.view').innerText")
        for m in MARKERS:
            if m in txt:
                hits.append((lab.strip(), m))
    b.close()

if hits:
    print("comment text is rendering (%d):" % len(hits))
    for s, m in hits:
        print("   %-24s %s" % (s, m))
else:
    print("No commented-out markup reached the page.")

raise SystemExit(1 if hits else 0)
