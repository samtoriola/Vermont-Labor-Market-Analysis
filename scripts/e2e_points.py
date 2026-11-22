"""Percentage points are labelled as points, everywhere they appear.

"Projected vs observed" subtracts one growth rate from another. Farming reads
+14.0 there because it is projected to rise 7.8% after falling 6.2% -- and
"+14.0%" on that bar invites a presenter to say the group is growing fourteen
percent, when it shrank. The caption named the unit; the numbers did not, and
the numbers are what gets read aloud.

So this checks the unit is on the marks, not only in the prose:
  - every bar label and axis tick on that measure ends in pp
  - the other three measures still end in %, because they ARE rates
  - Farming's bar equals its two inputs subtracted, to one decimal
  - the table carries the measure the chart draws, in the same unit

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
LC = json.load(open(os.path.join(HERE, "..", "data", "lightcast.json"), encoding="utf-8"))
FAMS = {r["f"]: r for r in LC["families"]}

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []
RATE_MEASURES = ["Change since 2021", "Projected growth"]
POINTS = "Projected vs observed"


def measure(pg, label):
    # Picker renders a bare .rankctl; only PickerPair wraps one in .ctlbar.
    pg.locator(".view .rankctl", has_text="Measure").locator(
        "button", has_text=re.compile("^%s$" % re.escape(label))).first.click()
    pg.wait_for_timeout(700)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1400}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.locator(".sbitem", has_text="Hiring and growth").first.click()
    pg.wait_for_timeout(900)

    # ---- the points measure ------------------------------------------------
    measure(pg, POINTS)
    vlabs = pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent.trim())")
    ticks = pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent.trim())")
    print("--- %s ---" % POINTS)
    print("  bars : %s" % ", ".join(vlabs[:4]))
    print("  ticks: %s" % ", ".join(ticks[:5]))

    if not vlabs:
        fails.append("no bar labels on %s at all" % POINTS)
    bad = [t for t in vlabs if not t.endswith(" pp")]
    if bad:
        fails.append("%s: bar labels not in points: %s" % (POINTS, bad[:4]))
    bad = [t for t in ticks if not t.endswith(" pp")]
    if bad:
        fails.append("%s: axis ticks not in points: %s" % (POINTS, bad[:5]))

    # The arithmetic the label stands for, against the committed data.
    labels = pg.eval_on_selector_all(
        ".view svg.chart text.clab", "els => els.map(e => e.textContent.trim())")
    checked = 0
    for short, shown in zip(labels, vlabs):
        row = [r for r in FAMS.values()
               if r["f"].startswith(short.split(" &")[0].split("…")[0][:12])]
        if len(row) != 1:
            continue
        checked += 1
        r = row[0]
        want = r["g5pct"] - r["chgPct"]
        got = float(shown.replace(" pp", "").replace("+", "").replace("−", "-"))
        if abs(got - want) > 0.05:
            fails.append("%s: shows %s, data says %+.1f (%.1f minus %.1f)"
                         % (r["f"], shown, want, r["g5pct"], r["chgPct"]))

    # Axis labels are truncated, so some rows will not resolve to a family. A
    # floor keeps the loop above from passing by matching nothing at all.
    print("  checked the arithmetic on %d of %d bars" % (checked, len(vlabs)))
    if checked < 8:
        fails.append("only %d bars resolved to a family: the arithmetic check is "
                     "not actually running" % checked)

    # The chart's own measure, in the table under it, in the same unit.
    pg.locator("button", has_text="Show the figures").first.click()
    pg.wait_for_timeout(600)
    # Headers carry a sort glyph (the current column a caret, the rest a pair of
    # arrows), so compare on the words alone.
    heads = pg.eval_on_selector_all(
        ".view table th", "els => els.map(e => e.textContent.trim().toLowerCase())")
    heads = [re.sub(r"[^a-z0-9 ]+$", "", h).strip() for h in heads]
    if "projected minus observed" not in heads:
        fails.append("the table does not carry the measure the chart draws: %s" % heads)
    else:
        i = heads.index("projected minus observed")
        cells = pg.eval_on_selector_all(
            ".view table tbody tr",
            "els => els.map(r => Array.from(r.querySelectorAll('td')).map(c => c.textContent.trim()))")
        col = [c[i] for c in cells if len(c) > i and c[i] != "—"]
        print("  table: %s" % ", ".join(col[:4]))
        bad = [t for t in col if not t.endswith(" pp")]
        if bad:
            fails.append("table column not in points: %s" % bad[:4])
    pg.locator("button", has_text="Hide the figures").first.click()
    pg.wait_for_timeout(400)

    # ---- the three that really are rates -----------------------------------
    for m in RATE_MEASURES:
        measure(pg, m)
        vlabs = pg.eval_on_selector_all(
            ".view svg.chart text.vlab", "els => els.map(e => e.textContent.trim())")
        print("--- %s ---\n  bars : %s" % (m, ", ".join(vlabs[:4])))
        bad = [t for t in vlabs if not t.endswith("%")]
        if bad:
            fails.append("%s: should still be a rate, got %s" % (m, bad[:4]))

    if errs:
        fails.append("page errors: %s" % errs[:2])
    b.close()

print()
if fails:
    for f in fails:
        print("FAIL  %s" % f)
    sys.exit(1)
print("OK  percentage points are labelled as points")
