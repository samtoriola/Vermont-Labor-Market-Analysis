"""The sector read-out against the measure and depth the reader picked.

Six combinations -- two measures by three depths -- each of which has to produce
its own line, name the slice it describes, and carry figures that match the ones
recomputed here from data/lightcast.json rather than from anything the page says.

The point of the independent recompute is that a read-out drawn from a slice is
only safe if it is the right slice. A line that silently kept reporting all 21
sectors while the chart showed 10 would look perfectly plausible.

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
SEC = LC["sectors"]                       # already jobs-descending, as the chart ranks it
TOT = LC["totalJobs"]

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []


def comma(n):
    return "{:,}".format(int(round(n)))


def o55(row):
    a = row["age"]
    t = sum(a.values())
    return a["o55"] / t, t


# The same two orderings the page builds: by jobs, and by the 55+ share.
BY_JOBS = list(SEC)
BY_AGE = sorted([r for r in SEC if r.get("age")], key=lambda r: -o55(r)[0])

TOP = len(SEC) // 2             # floor, as rankViews does; the spare row goes to the bottom


def shown_rows(rows, view):
    if view == "top":
        return rows[:TOP]
    if view == "bottom":
        return rows[TOP:]
    return rows


CASES = []
for view, label in (
    ("all", "All %d" % len(SEC)),
    ("top", "Top %d" % TOP),
    ("bottom", "Bottom %d" % (len(SEC) - TOP)),
):
    CASES.append(("Share of jobs", label, view))
    CASES.append(("Age mix", label, view))


def expected(measure, view):
    """The figures the line has to carry, recomputed from the source data."""
    rows = BY_JOBS if measure == "Share of jobs" else BY_AGE
    shown = shown_rows(rows, view)
    rest = [r for r in rows if r not in shown]

    if measure == "Share of jobs":
        s = sum(r["j"] for r in shown)
        if view == "all":
            return len(shown), [comma(TOT), rows[0]["s"], rows[1]["s"]]
        return len(shown), [comma(s)]

    num = sum(o55(r)[0] * o55(r)[1] for r in shown)
    den = sum(o55(r)[1] for r in shown)
    out = ["%.0f%%" % (num / den * 100), comma(num)]
    if rest:
        rn = sum(o55(r)[0] * o55(r)[1] for r in rest)
        rd = sum(o55(r)[1] for r in rest)
        out.append("%.0f%%" % (rn / rd * 100))
    return len(shown), out


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1600, "height": 1100}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.locator(".sbitem", has_text="Industry sectors").first.click()
    pg.wait_for_timeout(800)

    # Both chips live in one bar now, which is the whole point: the read-out
    # answers the pair, so the pair has to be readable as a pair.
    bar = pg.locator("#view-structure .ctlbar")
    if bar.count() != 1:
        fails.append("expected one combined control bar, found %d" % bar.count())
    # all_inner_texts reflects the CSS, which upper-cases these.
    labels = [t.strip().lower() for t in bar.locator(".sclab").all_inner_texts()]
    if labels != ["measure", "show"]:
        fails.append("control bar reads %r, wanted ['Measure', 'Show']" % labels)

    seen = {}
    for measure, depth, view in CASES:
        pg.locator(".ctlbar .rankctl", has_text="Measure").locator(
            "button", has_text=measure).first.click()
        pg.wait_for_timeout(350)
        pg.locator(".ctlbar .rankctl", has_text="Show").locator(
            "button", has_text=depth).first.click()
        pg.wait_for_timeout(450)

        note = pg.locator("#view-structure .pnote").first
        if not note.count():
            fails.append("%s / %s: no read-out" % (measure, depth))
            continue
        text = " ".join(note.inner_text().split())

        n_rows, want = expected(measure, view)

        # The chart has to be showing the rows the line is describing.
        drawn = pg.locator("#view-structure .split svg.chart g > text.clab").count()
        if drawn != n_rows:
            fails.append("%s / %s: chart drew %d rows, line describes %d"
                         % (measure, depth, drawn, n_rows))

        # It has to name its own scope, so a slice figure cannot read as a
        # statewide one.
        scope = "All %d sectors" % n_rows if view == "all" else "These %d sectors" % n_rows
        if scope.lower() not in text.lower():
            fails.append("%s / %s: line does not name its scope (%r)" % (measure, depth, scope))

        for w in want:
            if w not in text:
                fails.append("%s / %s: %r missing from %r" % (measure, depth, w, text))

        key = "%s|%s" % (measure, depth)
        seen[key] = text
        print("%-16s %-11s %s" % (measure, depth, text))

    # Six combinations, six distinct lines: if two match, one of them is not
    # responding to the control.
    if len(set(seen.values())) != len(seen):
        fails.append("the read-out repeats across combinations")

    b.close()

if errs:
    print("PAGE ERRORS:", errs)
print("")
print("FAIL: " + "; ".join(fails) if fails else "CLEAN")
sys.exit(1 if fails or errs else 0)
