"""Exact pooled ladder, the pane's third figure, and the legend. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))


def patch(rel, pairs):
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, "%s: %d occurrences of %r" % (rel, s.count(old), old[:70])
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(rel, "patched,", len(s), "bytes")


# ---- 1. exact rather than gridded ------------------------------------------
# A grid of 240 steps put the pooled high-school midpoint at $49,934 against an
# exact $49,996. On most figures $62 would not matter; on this one it is the
# whole finding -- the midpoint high-school job clears a living wage by about a
# hundred dollars a year -- so the figure has to be the real one.
#
# It does not need a finer grid. Each member's shareBelow() is linear in V
# between its own published percentiles, so the pooled curve is piecewise linear
# with a kink only where some member has one. Evaluate at exactly those points
# and the interpolation between them is exact, which is also cheaper than the
# grid it replaces.
patch("lib/wage.js", [(
    """ * HOW
 * ---
 * shareBelow() already answers "what share of this occupation's jobs sit under
 * $V". Summing it across the members weighted by employment gives the group's
 * share under $V, for any V. Walk a value grid, then read the grid backwards for
 * the V at each percentile we want. 240 steps holds the error under a tenth of a
 * percentile at this scale and keeps five rungs inside a frame.
 */
const STEPS = 240;
const pooledCache = new Map();""",
    """ * HOW
 * ---
 * shareBelow() already answers "what share of this occupation's jobs sit under
 * $V". Summing it across the members weighted by employment gives the group's
 * share under $V, for any V. Each member's answer is linear in V between its own
 * published percentiles, so the pooled curve is piecewise linear with a kink only
 * where some member has one. Evaluating at exactly those points -- the union of
 * every member's p10 to p90 -- makes the interpolation between them exact, and a
 * grid fine enough to match it would be slower.
 */
const pooledCache = new Map();"""
), (
    """  let lo = Infinity;
  let hi = -Infinity;
  members.forEach(([, xs]) => {
    lo = Math.min(lo, xs[0][0]);
    hi = Math.max(hi, xs[xs.length - 1][0]);
  });

  // [pay, share of the group's jobs below it], rising.
  const grid = [];
  for (let i = 0; i <= STEPS; i += 1) {
    const v = lo + ((hi - lo) * i) / STEPS;
    let s = 0;""",
    """  // Every pay value at which some member's curve bends, which is every value the
  // pooled curve can bend at too.
  const knots = new Set();
  members.forEach(([, xs]) => xs.forEach(([v]) => knots.add(v)));
  const vs = [...knots].sort((a, b) => a - b);

  // [pay, share of the group's jobs below it], rising.
  const grid = [];
  vs.forEach((v) => {
    let s = 0;"""
), (
    """      s += (j * q) / 100;
    });
    grid.push([v, (s / tot) * 100]);
  }""",
    """      s += (j * q) / 100;
    });
    grid.push([v, (s / tot) * 100]);
  });"""
)])

# ---- 2. the pane's figures, which the ladder rows carry differently ---------
# tierDetail built its three figures from an LC.tiers row. The ladder rows are
# built here instead, and their midpoint is the pooled one -- a different figure
# from LC.tiers[].med, which is the employment-weighted median of the member
# occupations' medians. Printing the pooled figure under the label "Typical pay"
# would put two different numbers under one name depending on which chip the
# reader is on, so the caller passes its own figures and its own labels.
patch("components/views/Q4.js", [(
    """  const tierDetail = (r) =>
    occDetail({
      label: 'Entry credential',
      title: r.t,
      occ: occByTier(r.t),
      lwAnnual: LWA,
      stats: [
        [fmt(r.jobs), 'Jobs today'],
        [r.share.toFixed(1) + '%', 'Of all VT jobs'],
        [r.med ? money(r.med) : '—', 'Typical pay'],
      ],
      onMore: () => tierDrill(r.t),
    });""",
    """  const tierDetail = (r, stats) =>
    occDetail({
      label: 'Entry credential',
      title: r.t,
      occ: occByTier(r.t),
      lwAnnual: LWA,
      stats: stats || [
        [fmt(r.jobs), 'Jobs today'],
        [r.share.toFixed(1) + '%', 'Of all VT jobs'],
        [r.med ? money(r.med) : '—', 'Typical pay'],
      ],
      onMore: () => tierDrill(r.t),
    });"""
), (
    """          <Legend
            labels={['Middle half of the work', 'Midpoint job', 'Lowest to highest-paid tenth']}
            colors={['--ord2', '--ord5', '--ord3']}
          />
          <Split items={ladder} keyOf={(r) => r.t} detail={(r) => tierDetail(r)}>""",
    """          {/* No legend. Three swatches cut from one ramp read as three shades of
              the same thing at 13px, and the caption already names the solid bar,
              the line and the heavy mark in the order the eye meets them. */}
          <Split
            items={ladder}
            keyOf={(r) => r.t}
            detail={(r) =>
              tierDetail(r, [
                [fmt(r.jobs), 'Jobs today'],
                [r.above.toFixed(0) + '%', 'Clears the benchmark'],
                [money(r.box.p50), 'The midpoint job'],
              ])
            }
          >"""
), (
    """import { Callout, HowTo, Legend, Panel, Picker, Table, VHead, LwPicker, N } from '../ui';""",
    """import { Callout, HowTo, Panel, Picker, Table, VHead, LwPicker, N } from '../ui';"""
)])
