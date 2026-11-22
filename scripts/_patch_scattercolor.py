"""Every occupation: colour the points that fall short of the benchmark.

The scatter already draws the benchmark as a vertical rule and the caption already
tells the reader that everything left of it falls short, but every point was the
same Ocean. The one comparison the chart exists to make was carried by position
alone, and on 796 points at r=4 a reader has to trace the line down the chart to
use it.

THE COLOUR CHOICE. lib/brand.js reserves GOOD/BAD -- Pine and Ember -- for exactly
this: marks that contrast two sides within one chart. But it also records that
Pine against Ember is 4.5 dE under deuteranopia, which is below the legible band,
and unlike the ranked bars a scatter carries no direct value labels to fall back
on. So only the shortfall takes Ember; the rest keeps Ocean, which the palette
validated as an adjacent pair. The vertical rule is the secondary encoding either
way -- every Ember point sits left of it.

The arithmetic is untouched. A point's x is its own median, which is the median
rule the tab argues against for SHARES of jobs; here it is correct, because the
point IS the occupation's typical job. The caption says so, and says the count is
occupations rather than jobs.

Checks every substitution before writing anything.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
EDITS = []


def edit(rel, pairs):
    EDITS.append((rel, pairs))


# ---------------------------------------------------------------- charts.js ---
edit("components/charts.js", [
    ("""      {pts.map((p, i) => (
        <TipMark key={i} title={p.label} rows={p.extra || []}>
          <circle
            cx={X(p.x)}
            cy={Y(p.y)}
            r={4}
            fill={V(SERIES[p.series])}""",
     """      {/* A point may name its own colour token, the way a bar row does, for the
          charts where the mark means something rather than belonging to a series. */}
      {pts.map((p, i) => (
        <TipMark key={i} title={p.label} rows={p.extra || []}>
          <circle
            cx={X(p.x)}
            cy={Y(p.y)}
            r={4}
            fill={V(p.color || SERIES[p.series])}"""),
])

# -------------------------------------------------------------------- Q2.js ---
edit("components/views/Q2.js", [
    # --- the import -------------------------------------------------------
    ("import { pricedPool, rollUp, rollUpBy } from '@/lib/wage';",
     "import { pricedPool, rollUp, rollUpBy } from '@/lib/wage';\nimport { BAD } from '@/lib/brand';"),

    # --- the doc block ----------------------------------------------------
    (""" * THE COLOUR
 * The filled part of every bar is Ocean, the house single-series colour, against the
 * --track remainder. It was Ember, on the reading that below-a-living-wage is the
 * semantic "bad" half of the GOOD/BAD pair in lib/brand.js. That was the wrong call
 * for a whole chart: red is a warning the reader is meant to act on, and a bar that
 * is 86% red reads as an alarm rather than a measurement. The same argument the
 * Overview makes for its ramp. The pair stays reserved for marks that genuinely
 * contrast two sides within one chart.
 */""",
     """ * THE COLOUR
 * The filled part of every bar is Ocean, the house single-series colour, against the
 * --track remainder. It was Ember, on the reading that below-a-living-wage is the
 * semantic "bad" half of the GOOD/BAD pair in lib/brand.js. That was the wrong call
 * for a whole chart: red is a warning the reader is meant to act on, and a bar that
 * is 86% red reads as an alarm rather than a measurement. The same argument the
 * Overview makes for its ramp. The pair stays reserved for marks that genuinely
 * contrast two sides within one chart.
 *
 * The scatter is that case. Its points are not a quantity shaded by degree but two
 * groups either side of the benchmark, which is the comparison the chart exists to
 * make, and it was asking position alone to carry it across 796 points. So the
 * shortfall takes Ember. The other half keeps Ocean rather than taking Pine: the
 * palette notes Pine against Ember is 4.5 dE under deuteranopia, and a scatter has
 * no value labels to fall back on the way the bars do. The rule is the secondary
 * encoding regardless -- every Ember point sits left of it.
 */"""),

    # --- the two counts the caption needs ---------------------------------
    ("""  const head = rollUp(filtered, LWA);""",
     """  const head = rollUp(filtered, LWA);

  // The scatter's rows: one point per occupation that has a median to plot. The
  // count of those falling short is of OCCUPATIONS, not jobs -- a point is one
  // occupation whatever its size, which is the whole reason the y-axis exists.
  const plotted = filtered.filter((o) => o.m);
  const shortOcc = plotted.filter((o) => o.m < LWA).length;"""),

    # --- the caption ------------------------------------------------------
    ("""                        cap={`${filtered.length === pool.length ? fmt(pool.length) : `${fmt(filtered.length)} of ${fmt(pool.length)}`} occupations, one point each. The vertical line is the living wage, so everything left of it is work whose typical job falls short.`}""",
     """                        cap={`${filtered.length === pool.length ? fmt(pool.length) : `${fmt(filtered.length)} of ${fmt(pool.length)}`} occupations, one point each. The vertical line is the living wage, and the points left of it — ${fmt(shortOcc)} of the ${fmt(plotted.length)} plotted — are work whose typical job falls short. That counts occupations, not jobs: one point is one occupation whatever its size, which is what the vertical axis is for.`}"""),

    # --- the legend and the points ----------------------------------------
    ("""                        <Scatter
                          pts={filtered
                            .filter((r) => r.m)
                            .map((r) => ({
                              x: r.m,
                              y: r.j,
                              label: r.n,
                              // One colour. The y-axis already is jobs, so shading
                              // the points by size band said the same thing twice,
                              // with no key, in three colours one of which was red.
                              series: 0,
                              extra: [
                                ['Median earnings', money(r.m)],
                                ['Jobs', fmt(r.j)],
                                ['Entry education', r.t],
                                ['Occupation group', r.f],
                              ],
                            }))}""",
     """                        <Legend
                          labels={['Typical job below the benchmark', 'At or above it']}
                          colors={[BAD, '--s1']}
                        />
                        <Scatter
                          pts={plotted.map((r) => ({
                            x: r.m,
                            y: r.j,
                            label: r.n,
                            // The colour is the benchmark, not a series: it says
                            // which side of the rule the point is on. Shading by
                            // size band, which this used to do, said what the
                            // y-axis already says, with no key and in three colours.
                            series: 0,
                            color: r.m < LWA ? BAD : '--s1',
                            extra: [
                              ['Median earnings', money(r.m)],
                              ['Against the benchmark', (r.m / LWA).toFixed(2) + '\\u00d7'],
                              ['Jobs', fmt(r.j)],
                              ['Entry education', r.t],
                              ['Occupation group', r.f],
                            ],
                          }))}"""),
])

# ------------------------------------------------------------------ apply ---
loaded = []
for rel, pairs in EDITS:
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _ in pairs:
        if s.count(old) != 1:
            raise SystemExit("%s: %d occurrences of %r" % (rel, s.count(old), old[:90]))
    loaded.append((p, rel, s, pairs))

for p, rel, s, pairs in loaded:
    for old, new in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("%-32s %d edits, %d bytes" % (rel, len(pairs), len(s)))
