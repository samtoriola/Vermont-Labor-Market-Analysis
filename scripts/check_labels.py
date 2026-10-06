"""Walk every section and report chart labels still drawn with an ellipsis.

A truncated axis label is the one defect a build cannot catch: it compiles, it
renders, and it reads as a mistake. This asks the browser which labels actually
got cut, at the widths the charts are really drawn at.
"""
import os
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3163")

cut = {}
seen = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1700, "height": 1000})
    pg.goto(URL)
    pg.wait_for_timeout(1800)
    labels = pg.eval_on_selector_all(".sbitem", "els => els.map(e => e.textContent)")
    for lab in labels:
        pg.locator(".sbitem", has_text=lab).first.click()
        pg.wait_for_timeout(700)
        found = pg.evaluate(
            """() => {
              const out = [];
              document.querySelectorAll('.panel svg.chart text').forEach(t => {
                const s = (t.textContent || '').trim();
                if (s.indexOf('\u2026') >= 0) out.push(s);
              });
              return out;
            }"""
        )
        for f in found:
            cut.setdefault(f, set()).add(lab)
        seen += pg.locator(".panel svg.chart text").count()

    b.close()

# A page that failed to hydrate has no chart text at all, and would otherwise
# report a clean pass. Nothing here is true unless the charts actually rendered.
assert seen > 200, "only %d chart labels found -- the app did not render" % seen
print("read %d chart labels" % seen)

if not cut:
    print("No truncated chart labels.")
else:
    print("Truncated chart labels (%d):" % len(cut))
    for text in sorted(cut):
        print("  %-40s on %s" % (text, ", ".join(sorted(cut[text]))[:70]))

raise SystemExit(1 if cut else 0)
