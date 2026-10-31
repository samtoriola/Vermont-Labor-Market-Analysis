"""The rebuilt Wage quality tab, checked against the arithmetic it claims to do.

The charts here are one number per row, so the way they go wrong is quietly: a
share read off the wrong thing still draws a plausible bar. This recomputes the
measure independently -- straight from data/lightcast.json and
data/percentiles.json, without importing anything the app uses -- and checks the
figures on screen against it.

  Every share the bars print is the benchmark's position along each occupation's
  own p10-p90 ladder, weighted by jobs. Not the median rule the tab used to use,
  which is wrong by 19 points on Installation & Repair.

  Share and headcount must reorder the chart. If they lead with the same row the
  second measure is not earning its chip, and on this data they do not: the
  highest share is Healthcare Support, the highest count is Food Preparation.

  The share bars sit on a 0-100 track, so a reader can see the remainder. The
  count bars must not -- a track on a ranked axis would end at the largest row
  and mean nothing.

  The county section is the only figure that comes out of a file rather than
  being computed live, so the bars must match data/wagefloor.json exactly, and
  switching the benchmark must move counties in both directions.

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


def D(name):
    with open(os.path.join(HERE, "..", "data", name), encoding="utf-8") as f:
        return json.load(f)


LC, PCT, WF = D("lightcast.json"), D("percentiles.json"), D("wagefloor.json")
LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]
PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]


def ladder(box):
    if not box:
        return None
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    return xs if len(xs) >= 2 else None


def share_below(xs, floor):
    if not xs:
        return None
    if floor <= xs[0][0]:
        return 0.0
    if floor >= xs[-1][0]:
        return 100.0
    for i in range(len(xs) - 1):
        (v0, q0), (v1, q1) = xs[i], xs[i + 1]
        if v0 <= floor <= v1:
            t = 0 if v1 == v0 else (floor - v0) / (v1 - v0)
            return q0 + t * (q1 - q0)
    return None


POOL = [o for o in LC["allOcc"] if ladder(PCT["occ"].get(o["s"]))]


def roll(occ):
    jobs = sum(o["j"] for o in occ)
    below = sum(o["j"] * share_below(ladder(PCT["occ"][o["s"]]), LWA) / 100 for o in occ)
    return jobs, below


def group_by(keyof):
    out = {}
    for o in POOL:
        out.setdefault(keyof(o), []).append(o)
    rows = []
    for k, occ in out.items():
        jobs, below = roll(occ)
        rows.append({"f": k, "jobs": jobs, "below": below / jobs * 100, "belowN": below})
    return rows


URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []


def chip(pg, group, label):
    pg.locator(".rankctl", has_text=group).first.locator(
        "button", has_text=label).first.click()
    pg.wait_for_timeout(700)


def labels(pg):
    return [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.clab", "els => els.map(e => e.textContent)")]


def values(pg):
    return [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")]


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1300}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem", has_text="Pay shortfall").first.click()
    pg.wait_for_timeout(1000)

    # ---- the headline the tab leads with --------------------------------
    jobs, below = roll(POOL)
    head = " ".join(pg.locator(".vhead p").first.inner_text().split())
    print("--- headline ---\n  %s" % head)
    for want in (format(int(round(below)), ","), "%.0f%%" % (below / jobs * 100)):
        if want not in head:
            fails.append("headline is missing %s" % want)

    # ---- occupation groups, both measures -------------------------------
    rows = group_by(lambda o: o["f"])
    by_share = sorted(rows, key=lambda r: -r["below"])
    by_count = sorted(rows, key=lambda r: -r["belowN"])
    print("--- occupation groups ---")
    print("  top by share %s (%.1f%%), top by count %s (%s)"
          % (by_share[0]["f"], by_share[0]["below"], by_count[0]["f"],
             format(int(round(by_count[0]["belowN"])), ",")))
    if by_share[0]["f"] == by_count[0]["f"]:
        fails.append("share and headcount lead with the same row, so one chip is redundant")

    chip(pg, "Measure", "Share of jobs below")
    n = pg.locator(".view svg.chart g.bar").count()
    print("  %d bars" % n)
    if n != len(rows):
        fails.append("groups/share: %d bars, expected %d" % (n, len(rows)))

    shown = values(pg)
    want_vals = {"%.1f%%" % r["below"] for r in rows}
    missing = [t for t in shown if t not in want_vals]
    print("  %d printed shares, %d not in the recomputed data" % (len(shown), len(missing)))
    if missing:
        fails.append("groups/share: printed values not reproducible: %s" % missing[:4])

    # Every bar on the same 0-100 track, so the remainder reads as the answer.
    tracks = pg.locator(".view svg.chart rect[fill='var(--track)']").count()
    print("  %d tracks behind %d bars" % (tracks, n))
    if tracks != n:
        fails.append("groups/share: %d tracks for %d bars" % (tracks, n))

    axis = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent)")]
    if "100%" not in axis:
        fails.append("groups/share: axis does not reach 100%% (%s)" % axis[:6])

    lead = labels(pg)[0] if labels(pg) else "-"
    if lead != by_share[0]["f"]:
        fails.append("groups/share: leads with %s, expected %s" % (lead, by_share[0]["f"]))

    chip(pg, "Measure", "People below")
    lead = labels(pg)[0] if labels(pg) else "-"
    print("  headcount leads with %s" % lead)
    if lead != by_count[0]["f"]:
        fails.append("groups/count: leads with %s, expected %s" % (lead, by_count[0]["f"]))
    shown = values(pg)
    want_vals = {format(int(round(r["belowN"])), ",") for r in rows}
    missing = [t for t in shown if t not in want_vals]
    if missing:
        fails.append("groups/count: printed counts not reproducible: %s" % missing[:4])
    tracks = pg.locator(".view svg.chart rect[fill='var(--track)']").count()
    print("  %d tracks on the headcount chart (expected 0)" % tracks)
    if tracks:
        fails.append("groups/count: %d tracks on a ranked axis" % tracks)

    # ---- the other row options still draw -------------------------------
    for rowopt, expect in (("Entry credential", len(group_by(lambda o: o["t"]))),
                           ("Largest occupations", 25)):
        chip(pg, "Rows", rowopt)
        n = pg.locator(".view svg.chart g.bar").count()
        print("--- %s ---\n  %d bars (expected %d)" % (rowopt, n, expect))
        if n != expect:
            fails.append("%s: %d bars, expected %d" % (rowopt, n, expect))
        if not pg.locator(".view .pnote").first.inner_text().strip():
            fails.append("%s: no read-out" % rowopt)

    chip(pg, "Rows", "Every occupation")
    pts = pg.locator(".view svg.chart circle").count()
    print("--- Every occupation ---\n  %d points" % pts)
    if pts < 500:
        fails.append("scatter: %d points, expected the priced pool" % pts)

    # ---- the benchmark, which is the only control besides the chips ------
    chip(pg, "Rows", "Occupation groups")
    chip(pg, "Measure", "Share of jobs below")
    before = values(pg)
    opts = pg.eval_on_selector_all("select option", "els => els.map(e => e.textContent)")
    pg.locator("select").first.select_option(
        label=[o for o in opts if "2 children" in o][0])
    pg.wait_for_timeout(900)
    after = values(pg)
    print("--- the benchmark drives the figures ---")
    print("  top share %s at one adult, %s at a larger household" % (before[:1], after[:1]))
    if before == after:
        fails.append("the household selector moved nothing, so the figures are precomputed")
    pg.locator("select").first.select_option(
        label=[o for o in opts if o.startswith("1 adult, no")][0])
    pg.wait_for_timeout(800)
    if values(pg) != before:
        fails.append("putting the benchmark back did not restore the figures")

    # The five-group filter bar the other tabs carried was taken off this one: the
    # rows are already the narrowing, and the benchmark is the question.
    groups = pg.locator(".view .fgroup").count()
    print("  filter groups on this tab: %d (expected 0)" % groups)
    if groups:
        fails.append("the filter bar is back on the wage tab (%d groups)" % groups)

    # ---- the controls are one bar, not two stacked rows -----------------
    barcount = pg.locator(".view .ctlbar").count()
    rowcount = pg.locator(".view .ctlbar .rankctl").count()
    print("--- controls ---")
    print("  %d control bar(s) holding %d chip rows" % (barcount, rowcount))
    if barcount != 1 or rowcount != 2:
        fails.append("Rows and Measure are not one control bar (%d bars, %d rows)"
                     % (barcount, rowcount))

    axis = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent)")]
    print("  axis: %s" % " ".join(axis[:5]))
    if [a for a in axis if a.endswith(".0%")]:
        fails.append("axis ticks still carry a decimal: %s" % axis[:5])

    # A scatter is a different chart, not a different measure of the same one, so
    # the Measure row has to go when it is on screen.
    chip(pg, "Rows", "Every occupation")
    if pg.locator(".view .ctlbar .rankctl").count() != 1:
        fails.append("the Measure control is still shown beside the scatter")
    chip(pg, "Rows", "Occupation groups")

    # ---- the counties ---------------------------------------------------
    pg.locator(".sbitem", has_text="County floors").first.click()
    pg.wait_for_timeout(900)
    C = WF["counties"]
    print("--- counties ---")
    for mode, key in (("Each county's own floor", "local"), ("One statewide floor", "state")):
        chip(pg, "Benchmark", mode)
        n = pg.locator(".view svg.chart g.bar").count()
        lead = labels(pg)[0] if labels(pg) else "-"
        top = sorted(C, key=lambda r: -r[key])[0]
        shown = values(pg)
        want_vals = {"%.1f%%" % r[key] for r in C}
        missing = [t for t in shown if t not in want_vals]
        print("  %-26s %d bars, leads with %s (expected %s), %d unmatched"
              % (mode, n, lead, top["c"], len(missing)))
        if n != len(C):
            fails.append("counties/%s: %d bars, expected %d" % (key, n, len(C)))
        if lead != top["c"]:
            fails.append("counties/%s: leads with %s, expected %s" % (key, lead, top["c"]))
        if missing:
            fails.append("counties/%s: printed values not in wagefloor.json: %s"
                         % (key, missing[:4]))

    # The pair only earns two chips if the floor actually reorders the map.
    moves = sorted(C, key=lambda r: r["local"] - r["state"])
    print("  biggest movers: %s %+.1f, %s %+.1f"
          % (moves[-1]["c"], moves[-1]["local"] - moves[-1]["state"],
             moves[0]["c"], moves[0]["local"] - moves[0]["state"]))
    note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    print("  read-out: %s" % note[:120])
    if not note:
        fails.append("counties: no read-out")

    b.close()

print("")
if errs:
    print("PAGE ERRORS:", errs[:3])
print("FAIL: " + "; ".join(fails) if fails or errs else "CLEAN")
sys.exit(1 if fails or errs else 0)
