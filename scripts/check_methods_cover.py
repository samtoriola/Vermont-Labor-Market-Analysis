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
# What each hidden sub-tab explained, and the words Methods has to keep for that
# to remain true.
#
# "What this map cannot show" is deliberately absent. Its content moved here and
# then the Not covered panel was removed, so the county limits -- statewide-only
# demand, county and survey areas not nesting, household income against a
# one-adult floor -- are no longer stated anywhere a reader can see. That is a
# decision, not an oversight, and this file is where it is written down.
NEED = {
  "How openings are defined": ["openings", "separations"],
  "How the index is built":   ["opportunity index", "percentile ranks"],
  "How completions were linked": ["linked completions", "proportion to their vermont employment"],
  "What this measures (jobs vs workers)": ["jobs vs workers", "compare shares, not levels"],
  # Kept from the removed Not covered list: it guards against reading a weak score
  # as a judgement on a program rather than on the market it sits in.
  "A low score is not a verdict": ["a low score is not a verdict", "labor demand does not price"],
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
