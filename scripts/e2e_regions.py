"""The county panels: four measures over one set of fourteen places.

Checks the things that would make these charts wrong rather than merely ugly.

  The grey Vermont bar is a reference, not a fifteenth county. On jobs and pay
  it must be there; on change it must not, because a state-level change next to
  county changes invites adding them up.

  Every cell of the concentration grid is drawn. A county-and-family pair that
  silently goes missing leaves a hole a reader reads as zero, and the grid has
  308 of them.

  The printed figures are the ones in data/counties.json, and they are printed
  only where the cell is a specialisation. A grid that prints 1.0 three hundred
  times has buried the eight that matter.

  The two smallest counties are outlined and named in the caption. Essex at 6.9x
  the state concentration in farming is sixty-three jobs; drawn plain it looks
  like the strongest finding on the page.

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
D = json.load(open(os.path.join(HERE, "..", "data", "counties.json"), encoding="utf-8"))
C = D["counties"]
ST = D["state"]
FAM = D["famOrder"]
THIN = [r for r in C if r["thin"]]
# Must track HEAT_PRINT_FROM in components/heatmap.js: the figure is printed
# on the darkest step only.
PRINT_AT = 1.75

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []


def money(n):
    return "$" + format(int(round(n)), ",")


def chip(pg, label):
    pg.locator(".rankctl", has_text="Measure").first.locator(
        "button", has_text=label).first.click()
    pg.wait_for_timeout(700)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1200}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem", has_text="Counties compared").first.click()
    pg.wait_for_timeout(900)

    # ---- the three ranked measures -------------------------------------
    RANKED = [
        # No Vermont bar on jobs: the state total is the counties' sum, not a
        # peer, and drawing it would squeeze all fourteen into the left third.
        ("Jobs", "emp", False, lambda v: format(v, ","), False),
        ("Typical pay", "med", True, money, False),
        ("Change since %d" % D["base"], "chg", False,
         lambda v: ("+" if v > 0 else "") + "%.1f%%" % v, True),
    ]
    for label, key, with_state, fmt, signed in RANKED:
        chip(pg, label)
        print("--- %s ---" % label)
        bars = pg.locator(".view svg.chart g.bar").count()
        labels = [t.strip() for t in
                  pg.eval_on_selector_all(".view svg.chart text.clab",
                                          "els => els.map(e => e.textContent)")]
        want = len(C) + (1 if with_state else 0)
        print("  %d bars, leads with %s" % (bars, labels[0] if labels else "-"))
        if bars != want:
            fails.append("%s: %d bars, expected %d" % (label, bars, want))
        if ("Vermont" in labels) != with_state:
            fails.append("%s: Vermont reference bar %s"
                         % (label, "present" if "Vermont" in labels else "missing"))

        top = sorted(C, key=lambda r: -r[key])[0]
        if labels and labels[0] != top["c"]:
            fails.append("%s: leads with %s, expected %s" % (label, labels[0], top["c"]))

        shown = pg.eval_on_selector_all(".view svg.chart text.vlab",
                                        "els => els.map(e => e.textContent)")
        want_vals = {fmt(r[key]) for r in C}
        if with_state:
            want_vals.add(fmt(ST[key]))
        missing = [t for t in shown if t not in want_vals]
        print("  %d printed values, %d unmatched" % (len(shown), len(missing)))
        if missing:
            fails.append("%s: printed values not in the data: %s" % (label, missing[:4]))

        note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
        print("  read-out: %s" % note[:110])
        if not note:
            fails.append("%s: no read-out" % label)

    # ---- the concentration grid ----------------------------------------
    chip(pg, "What it specialises in")
    print("--- concentration ---")
    cells = pg.locator(".view svg.chart g.bar").count()
    want_cells = len(C) * len(FAM)
    print("  %d cells (expected %d)" % (cells, want_cells))
    if cells != want_cells:
        fails.append("grid: %d cells, expected %d" % (cells, want_cells))

    printed = pg.eval_on_selector_all(".view svg.chart text.seglab",
                                      "els => els.map(e => e.textContent)")
    want_printed = sorted("%.1f" % r["lq"][f] for r in C for f in FAM
                          if r["lq"][f] is not None and r["lq"][f] >= PRINT_AT)
    print("  %d figures printed (expected %d)" % (len(printed), len(want_printed)))
    if sorted(printed) != want_printed:
        fails.append("grid: printed figures %s, expected %s"
                     % (sorted(printed)[:6], want_printed[:6]))

    marks = pg.locator(".view svg.chart .thinmark").count()
    print("  thin columns outlined: %d (expected %d)" % (marks, len(THIN)))
    if marks != len(THIN):
        fails.append("grid: %d thin marks, expected %d" % (marks, len(THIN)))

    cap = " ".join(pg.locator(".view .cap").first.inner_text().split())
    for r in THIN:
        if r["c"] not in cap:
            fails.append("grid: caption does not name the thin county %s" % r["c"])

    legend = pg.locator(".view .legend li").count()
    if legend != 5:
        fails.append("grid: %d legend steps, expected 5" % legend)

    note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    print("  read-out: %s" % note[:140])
    sharp = max((r for r in C if not r["thin"]),
                key=lambda r: max(v for v in r["lq"].values() if v is not None))
    if sharp["c"] not in note:
        fails.append("grid: read-out quotes a thin county rather than %s" % sharp["c"])

    # The figures table is the only place the counts behind a ratio are legible.
    pg.locator(".view .datatoggle").first.click()
    pg.wait_for_timeout(500)
    # Headers are CSS-uppercased and carry a sort glyph, so match on the text
    # rather than on how it is drawn.
    head = [h.strip().lower() for h in pg.locator(".view .paneldata th").all_inner_texts()]
    print("  table columns: %s" % ", ".join(head))
    if not any("jobs" in h for h in head):
        fails.append("grid table: no job count behind the ratio")

    b.close()

print("")
if errs:
    print("PAGE ERRORS:", errs[:3])
print("FAIL: " + "; ".join(fails) if fails or errs else "CLEAN")
sys.exit(1 if fails or errs else 0)
