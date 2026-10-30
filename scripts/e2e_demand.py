"""The General demand panel: what postings ask for, by place.

Checks the things that would make this chart lie rather than merely look odd:
every column reaching 100%, the shares matching data/demand.json rather than
whatever the page happens to render, the denominator being stated-only postings,
and the qualifications being on the chart rather than implied.

Two of those qualifications carry most of the weight:

  Postings per job, under every Vermont column. Without it Washington County's
  70% bachelor's reads as a labour market, when it is a county that posts 1.78
  times per job where Chittenden posts 0.57.

  The thin-sample outline. Grand Isle has 225 postings stating an education
  level, which is too few to split four ways; drawn plain it would look as solid
  as Chittenden's 32,000.

Both views are checked, because they cover Vermont differently: the compact one
folds ten counties into a rollup, the full one names all fourteen and therefore
drops the postings that carry no county at all.

Run against a dev or `next start` server on VT_PORT.
"""
import json
import os
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "..", "data", "demand.json"), encoding="utf-8"))
VT = [a for a in D["areas"] if a["k"] == "vt"][0]
NAMED = set(D["named"])

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

VIEWS = [
    ("4 largest + rest",
     [a for a in D["areas"] if a["grp"] != "county" or a["k"] in NAMED]),
    ("All 14 counties",
     [a for a in D["areas"] if a["grp"] != "rollup"]),
]


def chip(pg, group, label):
    pg.locator(".ctlbar .rankctl", has_text=group).locator(
        "button", has_text=label).first.click()
    pg.wait_for_timeout(700)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1200}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.locator(".sbitem", has_text="General demand").first.click()
    pg.wait_for_timeout(900)

    for view, expect in VIEWS:
        chip(pg, "Places", view)
        for measure, field, stated, order in CASES:
            chip(pg, "Measure", measure)
            tag = "%s / %s" % (view, measure)
            print("--- %s ---" % tag)

            legend = [t.strip() for t in pg.locator(".legend li").all_inner_texts()]
            if legend != order:
                fails.append("%s: legend %r, wanted %r" % (tag, legend, order))

            # One column per place, every one full height. A 100% stack that
            # stops short is a segment silently dropped.
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
            if len(heights) != len(expect):
                fails.append("%s: %d columns, expected %d"
                             % (tag, len(heights), len(expect)))
            if heights:
                lo, hi = min(heights.values()), max(heights.values())
                print("  %d columns, stack heights %.0f to %.0f" % (len(heights), lo, hi))
                if hi - lo > 2:
                    fails.append("%s: columns differ by %.0fpx, so they are not all 100%%"
                                 % (tag, hi - lo))

            # Printed shares have to be the ones in the data, out of the stated
            # denominator -- not out of all postings.
            shown = pg.eval_on_selector_all(
                ".view svg.chart text.seglab", "els => els.map(e => e.textContent)")
            want = set()
            for a in expect:
                for v in a[field]:
                    want.add("%.1f%%" % (v / a[stated] * 100))
            missing = [t for t in shown if t not in want]
            print("  %d printed shares, %d unmatched" % (len(shown), len(missing)))
            if missing:
                fails.append("%s: printed shares not in the data: %s" % (tag, missing[:4]))

            # Postings per job, on the Vermont columns only.
            notes = pg.eval_on_selector_all(
                ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")
            n_expected = sum(1 for a in expect if a["perJob"])
            if len(notes) != n_expected:
                fails.append("%s: %d per-job figures, expected %d"
                             % (tag, len(notes), n_expected))

            cap = " ".join(pg.locator(".view .cap").first.inner_text().split())
            if "state" not in cap.lower():
                fails.append("%s: caption does not say the denominator is stated-only" % tag)

            # Thin columns are drawn but outlined, and named in the caption.
            want_thin = sum(1 for a in expect if a.get("thin"))
            got_thin = pg.locator(".view svg.chart .thinmark").count()
            print("  thin columns marked: %d (expected %d)" % (got_thin, want_thin))
            if got_thin != want_thin:
                fails.append("%s: %d thin marks, expected %d" % (tag, got_thin, want_thin))
            for a in expect:
                if a.get("thin") and a["label"] not in cap:
                    fails.append("%s: caption does not name thin column %s" % (tag, a["label"]))

            # The full view cannot reconstruct Vermont -- some postings carry no
            # county -- so it has to say how many it leaves out.
            if view.startswith("All"):
                placed = sum(a["postings"] for a in expect if a["grp"] == "county")
                if placed < VT["postings"] and "no county" not in cap:
                    fails.append("%s: caption does not account for the %s unplaced postings"
                                 % (tag, f"{VT['postings'] - placed:,}"))

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
