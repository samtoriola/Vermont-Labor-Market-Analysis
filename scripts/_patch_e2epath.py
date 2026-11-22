"""Extends e2e_pathways.py to cover the openings section. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2e_pathways.py")
s = io.open(P, encoding="utf-8").read()

# ---- recompute the openings split alongside the ladder ---------------------
ANCHOR = """MONEY = lambda v: "$" + format(int(round(v)), ",")"""
assert s.count(ANCHOR) == 1
s = s.replace(ANCHOR, '''# A year's hiring at each credential, split by the benchmark. Same measure as the
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

MONEY = lambda v: "$" + format(int(round(v)), ",")''')

# ---- the checks, before the browser closes ---------------------------------
ANCHOR2 = """    b.close()

print("")"""
assert s.count(ANCHOR2) == 1
s = s.replace(ANCHOR2, '''    # ================= Which credentials pay =========================
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
            if len(cols) < 2 or "openings" not in cols[1].lower() or "\\u25be" not in cols[1]:
                fails.append("the table does not open sorted by openings: %s" % cols[:3])
            # The doors count the section used to lead with is kept here, where it
            # is the right answer to a different question.
            if not any("hiring" in x.lower() for x in dstats):
                fails.append("the table dropped the hires-and-pays count: %s" % dstats)
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(300)

    b.close()

print("")''')

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("e2e_pathways.py patched,", len(s), "bytes")
