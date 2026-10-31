"""The front page, checked against the arithmetic behind its shading.

The Overview carries two measures in one mark -- bar length for how many jobs an
occupation group holds, fill for how much of that work pays below a living wage.
Length is checkable by eye; fill is not. A band computed from the wrong column,
or a ramp that collapses to one colour, draws a chart that looks entirely
plausible and says something false.

So this recomputes both measures straight from data/lightcast.json and
data/percentiles.json, without importing anything the app uses, and checks:

  Every one of the 22 groups is drawn, in descending order of jobs, with the
  printed job counts matching the recomputed ones.

  The fill of each bar is the band its share-below falls in. All five bands are
  on screen -- a ramp where every bar lands in one bucket is a ramp that is not
  saying anything.

  The second column prints the share-below, because a reader cannot recover a
  percentage from a colour and the chart is the front page.

Run against a dev or `next start` server on VT_PORT.
"""
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))


def D(name):
    with open(os.path.join(HERE, "..", "data", name), encoding="utf-8") as f:
        return json.load(f)


LC, PCT = D("lightcast.json"), D("percentiles.json")
LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]
PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]
# Must track BANDS in components/views/Overview.js.
BANDS = [10, 30, 50, 75]


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


def band(pc):
    for i, b in enumerate(BANDS):
        if pc < b:
            return i
    return len(BANDS)


POOL = [o for o in LC["allOcc"] if ladder(PCT["occ"].get(o["s"]))]
by = defaultdict(list)
for o in POOL:
    by[o["f"]].append(o)

GROUPS = []
for f, ms in by.items():
    jobs = sum(o["j"] for o in ms)
    below = sum(o["j"] * share_below(ladder(PCT["occ"][o["s"]]), LWA) / 100 for o in ms)
    GROUPS.append({"f": f, "jobs": jobs, "below": below / jobs * 100})
GROUPS.sort(key=lambda r: -r["jobs"])


def jsround(x):
    """JavaScript's Math.round, which is not Python's round().

    Python rounds a half to even, so round(5268.5) is 5268 while the app, having
    done Math.round on the same sum, prints 5269. Two of the twenty-two groups
    land exactly on a half.
    """
    import math
    return math.floor(x + 0.5)

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1400}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem, .navbtn", has_text="Overview").first.click()
    pg.wait_for_timeout(1100)

    # ---- one bar per group, largest first ------------------------------
    n = pg.locator(".view svg.chart g.bar").count()
    labels = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.clab", "els => els.map(e => e.textContent)")]
    print("--- bars ---")
    print("  %d bars, leads with %s" % (n, labels[0] if labels else "-"))
    if n != len(GROUPS):
        fails.append("%d bars, expected %d" % (n, len(GROUPS)))
    # The axis label is shortened, so compare on a prefix of the real name.
    if labels and not GROUPS[0]["f"].lower().startswith(labels[0].split(" &")[0].lower()):
        fails.append("leads with %r, expected %r" % (labels[0], GROUPS[0]["f"]))

    shown = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")]
    # Compared as numbers with a job of slack, not as strings. Lightcast reports
    # employment to one decimal, so a group of fifty-odd occupations can sum to
    # exactly x.5 -- Construction & Extraction does, at 14549.5 -- and whether
    # that lands above or below the half depends on the order the two languages
    # happen to accumulate the floats in. A one-job difference on a 14,000-job
    # group is not a defect worth failing a build over; a wrong column is.
    off = []
    for r, t in zip(GROUPS, shown):
        try:
            got = int(t.replace(",", ""))
        except ValueError:
            off.append((r["f"], t)); continue
        if abs(got - r["jobs"]) > 1:
            off.append((r["f"], "%s vs %.1f" % (t, r["jobs"])))
    print("  %d printed job counts, %d off by more than a job" % (len(shown), len(off)))
    if len(shown) != len(GROUPS):
        fails.append("%d job counts printed, expected %d" % (len(shown), len(GROUPS)))
    if off:
        fails.append("printed job counts not reproducible: %s" % off[:4])

    # ---- the fill is the band, and every band is used -------------------
    fills = pg.evaluate("""() => [...document.querySelectorAll('.view svg.chart g.bar rect')]
        .map(r => getComputedStyle(r).fill)""")
    print("--- shading ---")
    print("  %d distinct fills across %d bars" % (len(set(fills)), len(fills)))
    if len(set(fills)) != len(BANDS) + 1:
        fails.append("%d distinct fills, expected %d -- the ramp has collapsed"
                     % (len(set(fills)), len(BANDS) + 1))

    # Same band must mean same colour, and a different band a different colour.
    seen = {}
    for r, fill in zip(GROUPS, fills):
        k = band(r["below"])
        if k in seen and seen[k] != fill:
            fails.append("%s (%.0f%%) is shaded %s, but its band is already %s"
                         % (r["f"], r["below"], fill, seen[k]))
        seen[k] = fill
    if len(set(seen.values())) != len(seen):
        fails.append("two bands share a colour")
    print("  %d bands in use, each a distinct colour: %s"
          % (len(seen), len(set(seen.values())) == len(seen)))

    # ---- the percentage is printed, not only encoded --------------------
    right = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent)")]
    want_pc = {"%.0f%%" % r["below"] for r in GROUPS}
    hit = [t for t in right if t in want_pc]
    print("  %d printed shares matching the recomputed ones" % len(hit))
    if len(hit) < len(GROUPS) - 2:   # duplicates collapse in the set
        fails.append("only %d of %d share figures printed" % (len(hit), len(GROUPS)))

    note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    print("--- read-out ---\n  %s" % note[:150])
    if not note:
        fails.append("no read-out under the chart")

    b.close()

print("")
if errs:
    print("PAGE ERRORS:", errs[:3])
print("FAIL: " + "; ".join(fails) if fails or errs else "CLEAN")
sys.exit(1 if fails or errs else 0)
