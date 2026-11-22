"""e2e_wage checks the scatter's colours, not just that points exist.

The points now carry the benchmark: left of the rule is Ember, right of it is
Ocean. That is a claim about every one of 781 marks, and the way it goes wrong is
silent -- an off-by-one comparison, or a colour that stops following the household
selector, still draws a plausible chart. So the split is recomputed here and
counted off the DOM, and the benchmark is moved to check the colours move with it.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "e2e_wage.py")
s = io.open(P, encoding="utf-8").read()

subs = [
    ("""    chip(pg, "Rows", "Every occupation")
    pts = pg.locator(".view svg.chart circle").count()
    print("--- Every occupation ---\\n  %d points" % pts)
    if pts < 500:
        fails.append("scatter: %d points, expected the priced pool" % pts)
""",
     """    chip(pg, "Rows", "Every occupation")
    pts = pg.locator(".view svg.chart circle").count()
    print("--- Every occupation ---\\n  %d points" % pts)
    if pts < 500:
        fails.append("scatter: %d points, expected the priced pool" % pts)

    # The colour is the benchmark: a point left of the rule is Ember, one at or
    # above it is Ocean. Recomputed here rather than read off the chart, so a
    # comparison that drifts by one occupation fails instead of still looking
    # plausible. The x-axis is the occupation's own median, which is the right
    # reading for a point that IS that occupation's typical job -- it is not the
    # ladder measure the bars use, and the two must not be confused.
    plotted = [o for o in POOL if o.get("m")]
    want_below = sum(1 for o in plotted if o["m"] < LWA)
    fills = pg.eval_on_selector_all(
        ".view svg.chart circle", "els => els.map(e => e.getAttribute('fill'))")
    got_below = fills.count("var(--bad)")
    got_above = fills.count("var(--s1)")
    print("  %d below the benchmark, %d at or above (expected %d / %d)"
          % (got_below, got_above, want_below, len(plotted) - want_below))
    if got_below != want_below or got_above != len(plotted) - want_below:
        fails.append("scatter colours: %d/%d on screen, %d/%d in the data"
                     % (got_below, got_above, want_below, len(plotted) - want_below))
    if got_below + got_above != len(fills):
        fails.append("scatter: %d points carry neither colour"
                     % (len(fills) - got_below - got_above))

    # A colour with no key is a colour nobody can read.
    key = pg.locator(".view .legend li").all_inner_texts()
    print("  legend: %s" % " | ".join(key))
    if len(key) != 2 or "below the benchmark" not in " ".join(key).lower():
        fails.append("the scatter's legend does not name the two sides: %s" % key)

    # Raising the benchmark must repaint points, or the colour was baked in at
    # build time and only looks like it follows the control.
    hopts = pg.eval_on_selector_all("select option", "els => els.map(e => e.textContent)")
    pg.locator("select").first.select_option(
        label=[o for o in hopts if "2 children" in o][0])
    pg.wait_for_timeout(900)
    raised = pg.eval_on_selector_all(
        ".view svg.chart circle", "els => els.map(e => e.getAttribute('fill'))"
    ).count("var(--bad)")
    print("  at a larger household: %d below (was %d)" % (raised, got_below))
    if raised <= got_below:
        fails.append("raising the benchmark did not turn more points red (%d -> %d)"
                     % (got_below, raised))
    pg.locator("select").first.select_option(
        label=[o for o in hopts if o.startswith("1 adult, no")][0])
    pg.wait_for_timeout(800)
"""),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("%d occurrences of %r" % (s.count(old), old[:90]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("e2e_wage.py patched,", len(s), "bytes")
