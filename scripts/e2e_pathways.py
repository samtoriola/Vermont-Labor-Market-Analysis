"""The credential ladder, checked against the arithmetic behind it.

The Pathways chart draws five pay ranges and prints two figure columns beside
them. None of that is checkable by eye: a ladder read off the wrong roll-up, or a
sufficiency figure computed by the rule this tab used to use, draws a chart that
looks entirely reasonable and says something false. Both of those were live on
this tab until the chart was rebuilt, so both are what this guards.

It recomputes everything straight from data/lightcast.json and
data/percentiles.json, importing nothing the app uses, and checks:

  Five rungs, in ladder order, with the printed midpoint matching the POOLED one
  -- the value V where half the rung's jobs pay less than V, built from the
  member occupations' own ladders weighted by employment.

  That the pooled ladder is what is drawn, and not percentiles.json's published
  tier ladder, which is the employment-weighted mean of its occupations'
  percentiles and understates the spread by up to 44%. The two are close enough
  to look right and far enough apart to be wrong, so the test pins the one the
  chart must not be using as well as the one it must.

  The share clearing the benchmark, read off each occupation's own distribution
  and rolled up -- not the median rule, which reported 100% for graduate /
  professional work when 2.2% of it falls short.

  That the benchmark selector moves the sufficiency column and leaves the pay
  ladder alone, because the ladder is a property of the work and the benchmark is
  a property of the household.

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
ORDER = ["No formal credential", "High school", "Sub-baccalaureate",
         "Bachelor's", "Graduate / professional"]


def ladder(box):
    if not box:
        return None
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    return xs if len(xs) >= 2 else None


def share_below(xs, v):
    if v <= xs[0][0]:
        return 0.0
    if v >= xs[-1][0]:
        return 100.0
    for i in range(len(xs) - 1):
        (v0, q0), (v1, q1) = xs[i], xs[i + 1]
        if v0 <= v <= v1:
            t = 0 if v1 == v0 else (v - v0) / (v1 - v0)
            return q0 + t * (q1 - q0)
    return None


def pooled(members):
    """The rung's own ladder.

    Each member's share_below is linear in V between its published percentiles,
    so the pooled curve bends only where some member does. Evaluating at exactly
    those points makes the interpolation between them exact -- the same thing
    pooledLadder() in lib/wage.js does, arrived at independently here.
    """
    ms = [(o["j"], ladder(PCT["occ"].get(o["s"]))) for o in members]
    ms = [(j, x) for j, x in ms if x and j > 0]
    if not ms:
        return None
    tot = sum(j for j, _ in ms)
    vs = sorted({v for _, x in ms for v, _ in x})
    curve = [(v, sum(j * share_below(x, v) for j, x in ms) / tot) for v in vs]
    out = {}
    for q, key in PTS:
        hit = None
        for i in range(len(curve) - 1):
            (v0, s0), (v1, s1) = curve[i], curve[i + 1]
            if s0 <= q <= s1:
                t = 0 if s1 == s0 else (q - s0) / (s1 - s0)
                hit = v0 + t * (v1 - v0)
                break
        out[key] = None if hit is None else round(hit)
    return out


by = defaultdict(list)
for o in LC["allOcc"]:
    if ladder(PCT["occ"].get(o["s"])):
        by[o["t"]].append(o)

RUNGS = []
for k in ORDER:
    ms = by[k]
    jobs = sum(o["j"] for o in ms)
    below = sum(o["j"] * share_below(ladder(PCT["occ"][o["s"]]), LWA) / 100 for o in ms)
    pub = PCT["tiers"].get(k, {})
    RUNGS.append({
        "t": k,
        "jobs": round(jobs),
        "box": pooled(ms),
        "pubP50": pub.get("p50"),
        "above": 100 - below / jobs * 100,
        # what the retired chart printed, kept so the test fails if it comes back
        "medianRule": LC["livingWage"] and next(
            r["above"][LC["defaultLW"]] for r in LC["tiers"] if r["t"] == k),
    })

# A year's hiring at each credential, split by the benchmark. Same measure as the
# ladder -- the benchmark's position on each occupation's own ladder -- weighted by
# openings instead of by jobs. Occupations with no published ladder are out of both
# sides, exactly as rollUpOn() drops them.
OPEN = []
for k in ORDER:
    tot = pay = 0.0
    n = 0
    for o in by[k]:
        if not o.get("o"):
            continue
        sb = share_below(ladder(PCT["occ"][o["s"]]), LWA)
        tot += o["o"]
        pay += o["o"] * (100 - sb) / 100
        n += 1
    # The screen this replaced: openings in occupations hiring 50+ a year whose
    # median clears the benchmark. Pinned so a revert is a failure, not a silence.
    gated = sum(o["o"] for o in LC["allOcc"]
                if o["t"] == k and (o.get("o") or 0) >= 50 and o.get("m") and o["m"] >= LWA)
    gatedAll = sum(o.get("o") or 0 for o in LC["allOcc"] if o["t"] == k)
    OPEN.append({"t": k, "openAll": round(tot), "openPay": round(pay),
                 "share": pay / tot * 100, "nocc": n,
                 "gatedShare": gated / gatedAll * 100 if gatedAll else None})

MONEY = lambda v: "$" + format(int(round(v)), ",")

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(90):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1300}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem", has_text="By credential level").first.click()
    pg.wait_for_timeout(1300)

    # ---- five rungs, in ladder order ------------------------------------
    labels = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.clab", "els => els.map(e => e.textContent)")]
    print("--- rungs ---")
    print("  %d drawn: %s" % (len(labels), " | ".join(labels)))
    if len(labels) != len(ORDER):
        fails.append("%d rungs drawn, expected %d" % (len(labels), len(ORDER)))
    for got, want in zip(labels, ORDER):
        # axis labels are shortened, so compare on the opening words
        if not want.lower().startswith(got.split(" /")[0].lower()[:10]):
            fails.append("rung order: got %r where %r belongs" % (got, want))

    # ---- the midpoint is the pooled one, not the published one -----------
    mids = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")]
    print("--- the midpoint of each rung ---")
    for r, shown in zip(RUNGS, mids):
        want, pub = r["box"]["p50"], r["pubP50"]
        try:
            got = int(shown.replace("$", "").replace(",", ""))
        except ValueError:
            fails.append("%s prints %r, not a figure" % (r["t"], shown))
            continue
        ok = abs(got - want) <= 1
        print("  %-24s %10s   pooled %10s   published %10s  %s"
              % (r["t"], shown, MONEY(want), MONEY(pub), "ok" if ok else "MISMATCH"))
        if not ok:
            fails.append("%s midpoint %s, pooled says %s" % (r["t"], shown, MONEY(want)))
        # The published roll-up is the wrong source for this chart, and on four of
        # the five rungs it is far enough away to be caught.
        if abs(pub - want) > 200 and abs(got - pub) <= 1:
            fails.append("%s is drawing the published tier ladder, not the pooled one" % r["t"])

    # ---- the two figure columns -----------------------------------------
    figs = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent)")]
    print("--- clears the benchmark ---")
    for r in RUNGS:
        want = "%.0f%%" % r["above"]
        old = "%.0f%%" % r["medianRule"]
        if want not in figs:
            fails.append("%s: no column printing %s (clears the benchmark)" % (r["t"], want))
        print("  %-24s %6s   median rule said %6s   jobs %9s"
              % (r["t"], want, old, format(r["jobs"], ",")))
        if format(r["jobs"], ",") not in figs:
            fails.append("%s: no column printing %s jobs" % (r["t"], format(r["jobs"], ",")))
    # The rule this tab used to use put graduate / professional at a flat 100%.
    if "100%" in figs and "%.0f%%" % RUNGS[-1]["above"] != "100%":
        fails.append("a rung prints 100% clearing the benchmark — the median rule is back")

    # ---- the benchmark is drawn, and the caption stays in plain words -----
    cap = " ".join(pg.locator(".view .cap").first.inner_text().split()).lower()
    rule = pg.evaluate(
        "() => [...document.querySelectorAll('.view svg.chart line')]"
        ".filter(l => l.getAttribute('stroke-dasharray')).length")
    print("--- the benchmark ---")
    print("  dashed rules drawn: %d" % rule)
    if not rule:
        fails.append("the benchmark is not ruled across the chart")
    for word in ("quartile", "whisker", "box plot", "interquartile"):
        if word in cap:
            fails.append("the caption says %r — this chart is described in plain words" % word)

    # ---- the selector moves sufficiency and leaves the ladder alone ------
    before_mid = mids[:]
    before_pc = [t for t in figs if t.endswith("%")]
    pg.locator("select").first.select_option(label="1 adult, 2 children — $63.91/hr")
    pg.wait_for_timeout(900)
    after_mid = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")]
    after_figs = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent)")]
    after_pc = [t for t in after_figs if t.endswith("%")]
    print("--- a larger household ---")
    print("  midpoints unchanged: %s" % (before_mid == after_mid))
    print("  clearing the benchmark: %s -> %s" % (before_pc[:5], after_pc[:5]))
    if before_mid != after_mid:
        fails.append("the pay ladder moved with the household — it is a property of the work")
    if before_pc == after_pc:
        fails.append("the household selector did not change the sufficiency column")
    pg.locator("select").first.select_option(label="1 adult, no children — $23.95/hr")
    pg.wait_for_timeout(700)

    # ---- the click-through -----------------------------------------------
    before_vb = pg.locator(".view svg.chart").first.get_attribute("viewBox")
    pg.locator(".view svg.chart g.bar").nth(3).click()
    pg.wait_for_timeout(800)
    pane = pg.locator(".view .detail")
    print("--- click-through ---")
    print("  pane open: %s" % (pane.count() > 0))
    if not pane.count():
        fails.append("clicking a rung opened no detail pane")
    else:
        stats = [" ".join(x.inner_text().split())
                 for x in pane.locator(".detail-stats > div").all()]
        print("  pane stats: %s" % " | ".join(stats))
        if len(stats) < 3:
            fails.append("the pane shows %d stats, expected 3" % len(stats))
        if any(s.startswith("—") for s in stats):
            fails.append("the pane prints an em dash where a figure belongs: %s" % stats)
        if not pane.locator(".morelink").count():
            fails.append("the pane offers no way through to the whole table")
        else:
            pane.locator(".morelink").click()
            pg.wait_for_timeout(800)
            dr = pg.locator(".drill")
            rows = dr.locator("tbody tr").count() if dr.count() else 0
            print("  full table opens: %s (%d rows)" % (dr.count() > 0, rows))
            if rows < 5:
                fails.append("the full table opened with %d rows" % rows)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(300)
    if pg.locator(".view svg.chart").first.get_attribute("viewBox") == before_vb:
        fails.append("the chart did not narrow to make room for the pane")

    # ================= Which credentials pay =========================
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    pg.locator(".sbitem", has_text="Which credentials pay").first.click()
    pg.wait_for_timeout(1200)

    print("--- a year of hiring ---")
    n = pg.locator(".view svg.chart g.bar").count()
    if n != len(ORDER):
        fails.append("%d bars on the openings chart, expected %d" % (n, len(ORDER)))
    figs = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent)")]
    vals = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")]
    for r in OPEN:
        want = format(r["openPay"], ",")
        pc = "%.0f%%" % r["share"]
        hit = any(abs(int(v.replace(",", "")) - r["openPay"]) <= 1
                  for v in vals if v.replace(",", "").isdigit())
        print("  %-24s %9s of %9s  %5s   (the gated measure said %4.0f%%)"
              % (r["t"], want, format(r["openAll"], ","), pc, r["gatedShare"]))
        if not hit:
            fails.append("%s: no bar printing %s openings in work that pays" % (r["t"], want))
        if pc not in figs:
            fails.append("%s: no column printing %s" % (r["t"], pc))
        # The measure this replaced is gated twice over and lands far lower. If it
        # comes back, the share column says so.
        gated = "%.0f%%" % r["gatedShare"]
        if gated != pc and gated in figs and pc not in figs:
            fails.append("%s prints the gated share %s — the volume screen is back" % (r["t"], gated))

    # The backdrop is that row's own total, so the bars sit inside it.
    widths = pg.evaluate(
        "() => [...document.querySelectorAll('.view svg.chart g.bar')]"
        ".map(g => [...g.querySelectorAll('rect')].map(r => +r.getAttribute('width')))")
    print("  every bar sits inside its own backdrop: %s"
          % all(len(w) >= 2 and w[0] >= w[1] - 0.5 for w in widths))
    for i, w in enumerate(widths):
        if len(w) < 2:
            fails.append("%s: no backdrop behind the bar" % ORDER[i])
        elif w[1] > w[0] + 0.5:
            fails.append("%s: bar is wider than its own openings total" % ORDER[i])

    note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    print("  read-out: %s" % note[:130])
    if not note:
        fails.append("no read-out under the openings chart")

    # ---- the click-through, all three levels ----------------------------
    before_vb = pg.locator(".view svg.chart").first.get_attribute("viewBox")
    pg.locator(".view svg.chart g.bar").first.click()
    pg.wait_for_timeout(800)
    pane = pg.locator(".view .detail")
    print("--- click-through ---")
    if not pane.count():
        fails.append("clicking an openings bar opened no pane")
    else:
        stats = [" ".join(x.inner_text().split())
                 for x in pane.locator(".detail-stats > div").all()]
        rows = pane.locator(".minitable tbody tr").count()
        print("  pane: %s | %d occupations" % (" | ".join(stats), rows))
        if len(stats) < 3:
            fails.append("the openings pane shows %d stats, expected 3" % len(stats))
        if not rows:
            fails.append("the openings pane lists no occupations")
        if pg.locator(".view svg.chart").first.get_attribute("viewBox") == before_vb:
            fails.append("the openings chart did not narrow for the pane")
        if not pane.locator(".morelink").count():
            fails.append("the openings pane offers no way to the whole table")
        else:
            pane.locator(".morelink").click()
            pg.wait_for_timeout(900)
            dr = pg.locator(".drill")
            cols = [t.strip() for t in pg.eval_on_selector_all(
                ".drill thead th", "els => els.map(e => e.textContent)")]
            dstats = [" ".join(x.inner_text().split()) for x in dr.locator(".dstat").all()]
            first = [t.strip() for t in pg.eval_on_selector_all(
                ".drill tbody tr:first-child td", "els => els.map(e => e.textContent)")]
            print("  table: %d rows, opens on %s" % (dr.locator("tbody tr").count(), cols[1]))
            print("  first row: %s" % " | ".join(first[:3]))
            if not dr.count():
                fails.append("the openings pane's link did not open the table")
            # Opened from a chart of openings, so it must land sorted by openings.
            if len(cols) < 2 or "openings" not in cols[1].lower() or "\u25be" not in cols[1]:
                fails.append("the table does not open sorted by openings: %s" % cols[:3])
            # The doors count the section used to lead with is kept here, where it
            # is the right answer to a different question.
            if not any("hiring" in x.lower() for x in dstats):
                fails.append("the table dropped the hires-and-pays count: %s" % dstats)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(300)

    b.close()

print("")
if errs:
    print("PAGE ERRORS:", errs[:3])
print("FAIL: " + "; ".join(fails) if fails or errs else "CLEAN")
sys.exit(1 if fails or errs else 0)
