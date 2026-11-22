"""Adds the ladder read-out and retires the two it replaces. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "insight.js")
s = io.open(P, encoding="utf-8").read()

ANCHOR = "/** The largest single credential category inside the tiers. */"
assert s.count(ANCHOR) == 1
assert "ladderShape" not in s

BLOCK = '''/**
 * The shape of the credential ladder, read off the pooled pay ranges.
 *
 * Replaces ladderStep() and livingWageJump(), which answered the same question on
 * two charts that no longer exist, and which read the published tier medians and
 * the median rule respectively. Both figures here come off the pooled ladder and
 * lib/wage.js, so the line and the chart cannot disagree.
 *
 * Says two things: which step is the real one, and where the benchmark actually
 * falls. The second matters more than it looks -- a rung whose midpoint clears by
 * a few hundred dollars is not a rung that pays a living wage.
 */
export function ladderShape(rows, lwAnnual, minStep = 8) {
  const v = rows.filter((r) => r.box && r.box.p50);
  if (v.length < 2) return null;
  let best = null;
  for (let i = 1; i < v.length; i += 1) {
    const d = v[i].above - v[i - 1].above;
    if (!best || d > best.d) best = { d, from: v[i - 1], to: v[i] };
  }
  // The rungs the benchmark falls inside: their midpoint clears it but a good part
  // of the work behind them does not, which is the finding a midpoint bar hides.
  const straddle = v.filter((r) => r.box.p25 < lwAnnual && lwAnnual < r.box.p75);
  const tight = v.filter(
    (r) => r.box.p50 >= lwAnnual && r.box.p50 - lwAnnual < 0.06 * lwAnnual
  );

  const parts = [];
  if (best && best.d >= minStep) {
    parts.push(
      `The step that changes the odds is ${shortLabel(best.from.t)} to ` +
      `${shortLabel(best.to.t)}: ${best.from.above.toFixed(0)}% of that work clears the ` +
      `benchmark, then ${best.to.above.toFixed(0)}%.`
    );
  } else {
    parts.push('No single rung changes the odds of clearing the benchmark at this household.');
  }
  if (tight.length) {
    const r = tight[0];
    parts.push(
      `The midpoint ${shortLabel(r.t).toLowerCase()} job pays ${money(r.box.p50)}, ` +
      `${money(r.box.p50 - lwAnnual)} over it.`
    );
  }
  if (straddle.length) {
    parts.push(
      `The benchmark falls inside the middle half of ${straddle.length} ` +
      `${straddle.length === 1 ? 'rung' : 'rungs'}, holding ` +
      `${fmt(straddle.reduce((a, r) => a + r.jobs, 0))} jobs.`
    );
  }
  return (best && best.d >= minStep ? found : none)(parts.join(' '));
}

'''
s = s.replace(ANCHOR, BLOCK + ANCHOR)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("insight.js patched,", len(s), "bytes")
