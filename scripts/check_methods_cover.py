"""Anything hidden must still be explained somewhere a reader can reach.

Several sub-tabs that only explained a measure are hidden, on the grounds that
Methods already defines them. That is only true for as long as Methods keeps
saying so, and nothing else would notice if an edit there dropped one -- the
build would pass and every page would render. This asserts the definitions are
still on the page.
"""
import os
from playwright.sync_api import sync_playwright
URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3163")
NEED = {
  "How openings are defined": ["openings", "separations"],
  "How the index is built":   ["opportunity index", "percentile ranks"],
  "How completions were linked": ["linked completions", "proportion to their vermont employment"],
  "What this map cannot show": ["demand by county", "do not nest", "household"],
  "What this measures (jobs vs workers)": ["jobs vs workers", "compare shares, not levels"],
}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width":1700,"height":1000})
    pg.goto(URL); pg.wait_for_timeout(1700)
    pg.locator(".sbitem.top", has_text="Methods").first.click(); pg.wait_for_timeout(1400)
    txt = pg.evaluate("() => document.querySelector('.view').innerText.toLowerCase()")
    bad = 0
    for topic, phrases in NEED.items():
        missing = [x for x in phrases if x not in txt]
        print("  %-42s %s" % (topic, "covered" if not missing else "MISSING " + str(missing)))
        bad += len(missing)
    print("Methods length:", len(txt), "chars")
    raise SystemExit(1 if bad else 0)
