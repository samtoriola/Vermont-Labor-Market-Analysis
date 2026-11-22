"""County living wage takes the benchmark picker.

wagefloor.json now carries all eight benchmarks per county, each computed the
same way, so the section can offer the household selector every other wage panel
has. Overlaying byLw[lw] onto each county row means the table columns, the
read-out and the bars keep reading `local` / `state` / `lwA` and none of them
had to change.

The caption's claim that one adult with no children was "the only household type
published per county" goes with it. It was never true.

Checks every substitution before writing anything.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "components", "views", "Q2.js")
s = io.open(P, encoding="utf-8").read()

subs = [
    # ---- the rows, resolved to the picked household -----------------------
    ("""  const cty = WF.counties;""",
     """  // Each county at the household the reader picked. byLw carries all eight,
  // each computed the same way as the default -- the benchmark's position on
  // every occupation's own ladder, weighted by its employment in that county --
  // so overlaying it leaves the bars, the table and the read-out reading the
  // same field names they always did.
  const cty = WF.counties.map((r) => ({ ...r, ...((r.byLw || {})[lw] || {}) }));
  const ctyRange = (WF.lwRangeBy || {})[lw] || WF.lwRange;
  const ctyFloor = (WF.stateLw || {})[lw] || WF.lwA;"""),

    # ---- the picker -------------------------------------------------------
    ("""                  The share of each county’s jobs paying below a living wage. Switch the
                  benchmark between the county’s own cost floor and one statewide figure,
                  and watch which counties move — a high-wage county with a high floor can
                  look better than it is on the statewide number.
                </HowTo>""",
     """                  The share of each county’s jobs paying below a living wage. Switch the
                  benchmark between the county’s own cost floor and one statewide figure,
                  and watch which counties move — a high-wage county with a high floor can
                  look better than it is on the statewide number. The household applies to
                  both floors at once, so changing it never muddles the comparison.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />"""),

    # ---- the captions -----------------------------------------------------
    ("""                          ? `Each county against its own living wage, which runs from ${money(WF.lwRange[0])} in the cheapest county to ${money(WF.lwRange[1])} in the dearest. Both benchmarks are one adult with no children — the only household type published per county — so the pair isolates geography and nothing else.${thinLine}`
                          : `Every county against the statewide ${money(WF.lwA)}, which is how the rest of the dashboard reads them. Switch to each county’s own floor to see what that assumption costs.${thinLine}`""",
     """                          ? `Each county against its own living wage for ${lw}, which runs from ${money(ctyRange[0])} in the cheapest county to ${money(ctyRange[1])} in the dearest. Both floors are the same household, so the pair isolates geography and nothing else.${thinLine}`
                          : `Every county against the statewide ${money(ctyFloor)} for ${lw}, which is how the rest of the dashboard reads them. Switch to each county’s own floor to see what that assumption costs.${thinLine}`"""),

    # ---- the source line --------------------------------------------------
    ("""· county living wage, one adult, no children`}""",
     """· county living wage, ${lw}`}"""),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("%d occurrences of %r" % (s.count(old), old[:90]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Q2.js patched,", len(s), "bytes")
