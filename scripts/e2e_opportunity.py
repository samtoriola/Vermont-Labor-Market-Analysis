"""The Opportunities tab, checked against the arithmetic behind both sections.

Highest scoring draws a composite as four stacked segments. Length is the score,
so a segment drawn from the wrong column, or scaled wrongly, still produces a bar
of the right length and a chart that is quietly false about what the score rests
on. So the segment widths are measured and compared with the ranks in sow.json.

Program candidates is a screen, and its chart's shade is the VSCS pipeline -- the
section's whole finding. That has two ways to go wrong without looking wrong: the
screen could drift from what lib/screen.js computes, and choosing a bar could fade
the shading out of the chart, which is the regression the Overview already had.
Both are asserted here.

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


LC, SOW = D("lightcast.json"), D("sow.json")
LWA = LC["livingWage"][LC["defaultLW"]] * LC["hours"]
O = SOW["opp"]
BYSOC = SOW["vscs"].get("bySoc", {})
COMPS = ["s_size", "s_growth", "s_postings", "s_pay"]

# The screen, recomputed from the JSON rather than imported. Mirrors
# opportunityScreen() in lib/screen.js at its defaults.
TIERS = ["Sub-baccalaureate", "Bachelor's"]
MIN_OPEN, THIN, GROWTH_FLOOR = 50, 0.08, 3
OBVIOUS = {r["soc"] for r in LC["topOcc"][:25]}


def med(xs):
    v = sorted(x for x in xs if x is not None)
    if not v:
        return 0
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2


BASE = [o for o in LC["allOcc"]
        if o.get("m") and o["m"] >= LWA and o.get("o") and o["o"] >= MIN_OPEN
        and o["t"] in TIERS and o["s"] not in OBVIOUS]
NORMS = {t: {"op": med([(o["o"] / o["j"]) * 100 for o in BASE if o["t"] == t and o.get("j")]),
             "post": med([(o["p"] / o["j"]) * 100 for o in BASE if o["t"] == t and o.get("j")])}
         for t in TIERS}
SCREEN = []
for o in BASE:
    n = NORMS.get(o["t"], {"op": 0, "post": 0})
    opr = (o["o"] / o["j"]) * 100 if o.get("j") else 0
    pr = (o["p"] / o["j"]) * 100 if o.get("j") else 0
    nsig = sum([opr > n["op"], pr > n["post"], (o.get("g") or 0) > GROWTH_FLOOR])
    sup = BYSOC.get(o["s"], {})
    linked = sup.get("linked", 0) or 0
    ratio = sup.get("ratio")
    SCREEN.append({"n": o["n"], "o": round(o["o"]), "linked": linked, "nsig": nsig,
                   "pipe": ("none" if linked == 0
                            else "thin" if (ratio is not None and ratio < THIN)
                            else "est")})
SCREEN.sort(key=lambda r: -r["o"])
NO_PIPE = [r for r in SCREEN if r["pipe"] == "none"]

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
    pg = b.new_context(viewport={"width": 1680, "height": 1400}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")

    # ================= Highest scoring ===================================
    pg.locator(".sbitem", has_text="Highest scoring").first.click()
    pg.wait_for_timeout(1400)
    print("--- the score, unpacked ---")

    segs = pg.evaluate(
        "() => [...document.querySelectorAll('.view svg.chart g.bar rect')]"
        ".map(r => +r.getAttribute('width'))")
    labels = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.clab", "els => els.map(e => e.textContent)")]
    print("  %d rows, %d segments" % (len(labels), len(segs)))
    if len(segs) != len(labels) * 4:
        fails.append("%d segments over %d rows, expected four each" % (len(segs), len(labels)))

    # Each segment is one rank's quarter, so within a row their widths are in the
    # same proportions as the ranks. Compared as ratios, which is independent of
    # whatever plot width the chart happens to be drawn at.
    off = []
    for i, lab in enumerate(labels[: len(segs) // 4]):
        row = [r for r in O["top"] if r["n"].startswith(lab.split("…")[0][:18])]
        if not row:
            continue
        want = [row[0][k] for k in COMPS]
        got = segs[i * 4:(i + 1) * 4]
        if not sum(got):
            off.append((lab, "zero width"))
            continue
        scale = sum(want) / sum(got)
        for w, g in zip(want, got):
            if abs(g * scale - w) > 1.5:
                off.append((lab, "%.0f vs %.0f" % (g * scale, w)))
                break
    print("  %d rows whose segments are not their four ranks" % len(off))
    if off:
        fails.append("segments do not match the ranks: %s" % off[:3])

    scores = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")]
    print("  score column: %s" % scores[:4])
    if any("%" in x for x in scores):
        fails.append("the score column prints a percentage: %s" % scores[:3])
    want_sc = {"%.1f" % r["sc"] for r in O["top"]}
    if len([x for x in scores if x in want_sc]) < len(scores) - 1:
        fails.append("printed scores are not the ones in sow.json: %s" % scores[:4])

    fills = pg.evaluate(
        "() => [...new Set([...document.querySelectorAll('.view svg.chart g.bar rect')]"
        ".map(r => r.getAttribute('fill')))].length")
    print("  distinct segment colours: %d" % fills)
    if fills != 4:
        fails.append("%d segment colours, expected four" % fills)

    # Two views of a ranking have to be two ends of it. Top 20 over a pool of 30
    # was not -- the slices shared ten rows and the chart looked fine either way.
    ctl = pg.locator(".rankctl", has_text="Show").first
    if ctl.count():
        def drawn():
            return [t.strip() for t in pg.eval_on_selector_all(
                ".view svg.chart text.clab", "els => els.map(e => e.textContent)")]
        ctl.locator("button", has_text="Top").first.click()
        pg.wait_for_timeout(600)
        top_rows = drawn()
        ctl.locator("button", has_text="Bottom").first.click()
        pg.wait_for_timeout(600)
        bottom_rows = drawn()
        shared = set(top_rows) & set(bottom_rows)
        print("  show control: top %d, bottom %d, sharing %d"
              % (len(top_rows), len(bottom_rows), len(shared)))
        if shared:
            fails.append("the top and bottom views share %d rows: %s"
                         % (len(shared), sorted(shared)[:3]))
        ctl.locator("button", has_text="Top").first.click()
        pg.wait_for_timeout(600)

    pg.locator(".view svg.chart g.bar").nth(5).click()
    pg.wait_for_timeout(700)
    pane = pg.locator(".view .detail")
    if not pane.count():
        fails.append("clicking a scored bar opened no pane")
    else:
        mini = [" ".join(t.split()) for t in pane.locator(".minitable tbody tr").all_inner_texts()]
        print("  pane: %s" % " | ".join(
            " ".join(x.inner_text().split()) for x in pane.locator(".detail-stats > div").all()))
        print("  the four ranks: %s" % mini)
        if len(mini) != 4:
            fails.append("the pane shows %d components, expected four" % len(mini))
        if not pane.locator(".morelink").count():
            fails.append("the scored pane offers no way through to its group")
    ops = pg.evaluate(
        "() => [...new Set([...document.querySelectorAll('.view svg.chart g.bar rect')]"
        ".filter(r => (r.getAttribute('fill') || '').startsWith('var'))"
        ".map(r => getComputedStyle(r).fillOpacity))]")
    print("  fill-opacities with a bar chosen: %s" % sorted(ops))
    if any(float(o) < 1 for o in ops):
        fails.append("choosing a bar faded the segments, which are the measure")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(250)

    # ================= Program candidates ================================
    pg.locator(".sbitem", has_text="Program candidates").first.click()
    pg.wait_for_timeout(1400)
    print("--- the screen ---")

    bars = pg.locator(".view svg.chart g.bar").count()
    rows = pg.locator(".view .dt tbody tr, .view table tbody tr").count()
    print("  %d bars drawn, %d rows on the table's first page, %d clear the screen"
          % (bars, rows, len(SCREEN)))
    if not bars:
        fails.append("the screen drew no bars")
    note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    print("  read-out: %s" % note[:170])
    if str(len(SCREEN)) not in note:
        fails.append("the read-out does not say how many clear the screen (%d)" % len(SCREEN))
    if str(len(NO_PIPE)) not in note:
        fails.append("the read-out does not carry the no-pipeline count (%d)" % len(NO_PIPE))

    figs = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent)")]
    shown = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")]
    top = SCREEN[:bars]
    for r in top[:6]:
        if format(r["o"], ",") not in shown:
            fails.append("%s: no bar printing %s openings" % (r["n"], format(r["o"], ",")))
    # A zero pipeline reads as a word, not as 0.0 -- the point of the column.
    if any(r["pipe"] == "none" for r in top) and "none" not in figs:
        fails.append("no row prints 'none' where VSCS produces nobody")
    print("  graduates column carries 'none': %s" % ("none" in figs))

    fills = pg.evaluate(
        "() => [...new Set([...document.querySelectorAll('.view svg.chart g.bar rect')]"
        ".map(r => r.getAttribute('fill')).filter(f => f && f.startsWith('var')))]")
    print("  distinct bar shades: %d" % len(fills))
    if len(fills) < 2:
        fails.append("the bars are one colour — the pipeline shading is gone")

    pg.locator(".view svg.chart g.bar").nth(2).click()
    pg.wait_for_timeout(700)
    pane = pg.locator(".view .detail")
    if not pane.count():
        fails.append("clicking a candidate opened no pane")
    else:
        mini = [" ".join(t.split()) for t in pane.locator(".minitable tbody tr").all_inner_texts()]
        print("  pane: %s" % " | ".join(
            " ".join(x.inner_text().split()) for x in pane.locator(".detail-stats > div").all()))
        print("  signals: %s" % mini)
        if len(mini) != 3:
            fails.append("the candidate pane shows %d signal tests, expected three" % len(mini))
    ops = pg.evaluate(
        "() => [...new Set([...document.querySelectorAll('.view svg.chart g.bar rect')]"
        ".filter(r => (r.getAttribute('fill') || '').startsWith('var'))"
        ".map(r => getComputedStyle(r).fillOpacity))]")
    print("  fill-opacities with a bar chosen: %s" % sorted(ops))
    if any(float(o) < 1 for o in ops):
        fails.append("choosing a candidate faded the pipeline shading")
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(250)

    # The controls still drive the screen.
    before = pg.locator(".view svg.chart g.bar").count()
    pg.locator(".screenctl .chips button", has_text="100+").first.click()
    pg.wait_for_timeout(900)
    after_note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    tighter = len([o for o in LC["allOcc"]
                   if o.get("m") and o["m"] >= LWA and (o.get("o") or 0) >= 100
                   and o["t"] in TIERS and o["s"] not in OBVIOUS])
    print("  at 100+ openings: read-out says %s, recomputed %d"
          % (after_note.split(" of ")[0], tighter))
    if str(tighter) not in after_note:
        fails.append("raising the minimum openings did not move the screen to %d" % tighter)

    b.close()

print("")
if errs:
    print("PAGE ERRORS:", errs[:3])
print("FAIL: " + "; ".join(fails) if fails or errs else "CLEAN")
sys.exit(1 if fails or errs else 0)
