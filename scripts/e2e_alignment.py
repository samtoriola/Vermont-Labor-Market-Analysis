"""VSCS alignment, checked against the denominator it is supposed to divide by.

The chart measures each occupation group's VSCS graduates against the openings
whose entry credential is one VSCS awards, rather than against every opening it
has. Both versions draw a plausible chart -- same bars, same groups, different
lengths and a different order -- so the only way to tell which one is on screen
is to recompute both and check which the printed shares match. This pins the one
that must be drawn and the one that must not.

It also checks the floor. Lightcast models openings to a fraction, so food
preparation carries 0.3 credential-requiring openings a year; on a bare "greater
than zero" test it joins Sales and Legal as though a 0.3-opening base were the
same kind of finding as a 201-opening one.

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


LC, SOW = D("lightcast.json"), D("sow.json")
V = SOW["vscs"]
# Must track VSCS_TIERS in lib/data.js and CRED in scripts/build_sow.py.
CRED = {"Sub-baccalaureate", "Bachelor's", "Graduate / professional"}
MIN_OPEN = 10

cred = defaultdict(float)
for o in LC["allOcc"]:
    if o["t"] in CRED:
        cred[o["f"]] += o.get("o") or 0

ROWS = []
for r in V["byFamily"]:
    oc = cred.get(r["f"], 0.0)
    ROWS.append({
        "f": r["f"], "linked": r["linked"], "openCred": oc, "openAll": r["open"],
        "ratio": (r["linked"] / oc * 100) if oc else None,
        "ratioAll": (r["linked"] / r["open"] * 100) if r["open"] else None,
    })
DRAWN = sorted([r for r in ROWS if r["openCred"] >= MIN_OPEN],
               key=lambda r: -r["ratio"])
OFF = [r for r in ROWS if r["openCred"] < MIN_OPEN]
TOTAL = sum(r["openCred"] for r in ROWS)
BARE = [r for r in DRAWN if not r["linked"]]

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
    pg.locator(".sbitem", has_text="Against demand").first.click()
    pg.wait_for_timeout(1400)

    # ---- the right groups, in the right order ---------------------------
    labels = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.clab", "els => els.map(e => e.textContent)")]
    print("--- the chart ---")
    print("  %d bars, leads with %s" % (len(labels), labels[0] if labels else "-"))
    if len(labels) != len(DRAWN):
        fails.append("%d bars, expected %d" % (len(labels), len(DRAWN)))
    if labels and not DRAWN[0]["f"].lower().startswith(labels[0].split(" &")[0].lower()[:10]):
        fails.append("leads with %r, expected %r" % (labels[0], DRAWN[0]["f"]))

    # ---- the share is against the credential-requiring openings ---------
    shown = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")]
    figs = [t.strip() for t in pg.eval_on_selector_all(
        ".view svg.chart text.nbadge", "els => els.map(e => e.textContent)")]
    print("--- which denominator ---")
    wrong = []
    for r, got in zip(DRAWN, shown):
        want = "%.0f%%" % r["ratio"]
        alt = "%.0f%%" % r["ratioAll"] if r["ratioAll"] is not None else None
        if got != want:
            wrong.append((r["f"], got, want, alt))
        if got == alt and alt != want:
            fails.append("%s prints %s — that is the share of ALL its openings" % (r["f"], got))
    for r in DRAWN[:5]:
        print("  %-38s %5s   (against all openings it would read %4s)"
              % (r["f"][:38], "%.0f%%" % r["ratio"],
                 "—" if r["ratioAll"] is None else "%.0f%%" % r["ratioAll"]))
    if wrong:
        fails.append("printed shares do not match the recomputed ones: %s" % wrong[:3])
    # the openings column beside each bar
    missing = [r["f"] for r in DRAWN[:8]
               if format(int(round(r["openCred"])), ",") not in figs]
    if missing:
        fails.append("no openings column for %s" % missing[:3])
    print("  openings column present for the top eight: %s" % (not missing))

    # ---- what is held off the chart, and why ----------------------------
    nc = pg.locator(".view .nocred")
    print("--- below the floor ---")
    if not nc.count():
        fails.append("the groups with no base to divide by are not named")
    else:
        txt = " ".join(nc.first.inner_text().split())
        print("  %s" % txt[:150])
        for r in OFF:
            if r["f"] not in txt:
                fails.append("%s is neither drawn nor named" % r["f"])
        for r in DRAWN:
            if r["f"] in txt:
                fails.append("%s is drawn and also named as having no base" % r["f"])

    # ---- the read-out names the real gaps, not the fractional ones ------
    note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    print("--- read-out ---\n  %s" % note[:200])
    if format(int(round(TOTAL)), ",") not in note:
        fails.append("the read-out does not carry the %s total" % format(int(round(TOTAL)), ","))
    for r in BARE:
        if r["f"].split(" &")[0] not in note:
            fails.append("the read-out does not name %s, which has a base and no graduates" % r["f"])
    for r in OFF:
        if r["f"].split(" &")[0] in note and r["f"] not in [x["f"] for x in BARE]:
            fails.append("the read-out names %s, whose base is below the floor" % r["f"])

    # ---- the table keeps every group and both denominators --------------
    pg.locator(".view button", has_text="Show the figures").first.click()
    pg.wait_for_timeout(700)
    heads = [t.strip().lower() for t in pg.eval_on_selector_all(
        ".view table thead th", "els => els.map(e => e.textContent)")]
    rows = pg.locator(".view table tbody tr").count()
    print("--- the figures ---")
    print("  %d rows, columns: %s" % (rows, " / ".join(heads)[:160]))
    if rows < len(ROWS):
        fails.append("the table shows %d groups, expected all %d" % (rows, len(ROWS)))
    if not any("ask" in h for h in heads):
        fails.append("the table does not carry the credential-requiring openings column")
    if not any("all openings" in h for h in heads):
        fails.append("the table dropped the all-openings column, which is the contrast")

    # ---- the click-through ----------------------------------------------
    before = pg.locator(".view svg.chart").first.get_attribute("viewBox")
    pg.locator(".view svg.chart g.bar").nth(2).click()
    pg.wait_for_timeout(800)
    pane = pg.locator(".view .detail")
    print("--- click-through ---")
    if not pane.count():
        fails.append("clicking a group opened no pane")
    else:
        stats = [" ".join(x.inner_text().split())
                 for x in pane.locator(".detail-stats > div").all()]
        print("  pane: %s" % " | ".join(stats))
        if len(stats) < 3:
            fails.append("the pane shows %d figures, expected 3" % len(stats))
        if not pane.locator(".morelink").count():
            fails.append("the pane offers no way through to the whole table")
    if pg.locator(".view svg.chart").first.get_attribute("viewBox") == before:
        fails.append("the chart did not narrow for the pane")
    ops = pg.evaluate(
        "() => [...new Set([...document.querySelectorAll('.view svg.chart g.bar rect')]"
        ".filter(r => (r.getAttribute('fill') || '').startsWith('var'))"
        ".map(r => getComputedStyle(r).fillOpacity))]")
    print("  fill-opacities with a bar chosen: %s" % sorted(ops))
    if any(float(o) < 1 for o in ops):
        fails.append("choosing a bar faded the shading that marks an absent pipeline")

    b.close()

print("")
if errs:
    print("PAGE ERRORS:", errs[:3])
print("FAIL: " + "; ".join(fails) if fails or errs else "CLEAN")
sys.exit(1 if fails or errs else 0)
