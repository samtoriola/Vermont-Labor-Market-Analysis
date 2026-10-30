"""The General demand panel: what postings ask for, by place.

Checks the things that would make this chart lie rather than merely look odd:
every column reaching 100%, the shares matching data/demand.json rather than
whatever the page happens to render, the denominator being stated-only postings,
and the postings-per-job figure being present on the Vermont columns -- without
it, Washington County's height reads as demand when it is posting intensity.

Run against a dev or `next start` server on VT_PORT.
"""
import json
import os
import re
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "..", "data", "demand.json"), encoding="utf-8"))

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []

CASES = [("Education", "edu", "eduStated", D["eduOrder"]),
         ("Experience", "exp", "expStated", D["expOrder"])]

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1150}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.locator(".sbitem", has_text="General demand").first.click()
    pg.wait_for_timeout(900)

    for measure, field, stated, order in CASES:
        pg.locator(".rankctl .chips button", has_text=measure).first.click()
        pg.wait_for_timeout(700)
        print("--- %s ---" % measure)

        legend = [t.strip() for t in pg.locator(".legend li").all_inner_texts()]
        if legend != order:
            fails.append("%s: legend %r, wanted %r" % (measure, legend, order))

        # One column per place, and every one of them full height. A 100% stack
        # that stops short is a segment silently dropped.
        heights = pg.evaluate(
            """() => {
                 const by = {};
                 document.querySelectorAll('.view svg.chart g.bar rect').forEach(r => {
                   const x = r.getAttribute('x');
                   by[x] = (by[x] || 0) + parseFloat(r.getAttribute('height'));
                 });
                 return by;
               }"""
        )
        if len(heights) != len(D["areas"]):
            fails.append("%s: %d columns, expected %d" % (measure, len(heights), len(D["areas"])))
        if heights:
            lo, hi = min(heights.values()), max(heights.values())
            print("  %d columns, stack heights %.0f to %.0f" % (len(heights), lo, hi))
            if hi - lo > 2:
                fails.append("%s: columns differ by %.0fpx, so they are not all 100%%"
                             % (measure, hi - lo))

        # The printed shares have to be the ones in the data, out of the stated
        # denominator -- not out of all postings.
        shown = pg.eval_on_selector_all(
            ".view svg.chart text.seglab", "els => els.map(e => e.textContent)")
        want = set()
        for a in D["areas"]:
            for v in a[field]:
                pc = v / a[stated] * 100
                if pc >= 0:
                    want.add("%.1f%%" % pc)
        missing = [t for t in shown if t not in want]
        print("  %d printed shares, %d unmatched" % (len(shown), len(missing)))
        if missing:
            fails.append("%s: printed shares not in the data: %s" % (measure, missing[:4]))

        # Postings per job, on the Vermont columns only.
        notes = pg.eval_on_selector_all(
            ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")
        n_expected = sum(1 for a in D["areas"] if a["perJob"])
        if len(notes) != n_expected:
            fails.append("%s: %d per-job figures, expected %d"
                         % (measure, len(notes), n_expected))
        print("  per-job figures: %s" % " ".join(notes))

        cap = pg.locator(".view .cap").first.inner_text()
        if "state" not in cap.lower():
            fails.append("%s: caption does not say the denominator is stated-only" % measure)

    # The read-out has to name the denominator too, not just the caption.
    note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    print("\nread-out: %s" % note)
    if "state one" not in note:
        fails.append("read-out does not qualify the denominator")

    b.close()

if errs:
    print("PAGE ERRORS:", errs)
print("")
print("FAIL: " + "; ".join(fails) if fails else "CLEAN")
sys.exit(1 if fails or errs else 0)
