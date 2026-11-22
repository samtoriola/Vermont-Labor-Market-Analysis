"""Adds the ladder table columns. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "tables.js")
s = io.open(P, encoding="utf-8").read()

ANCHOR = "export function bandCols(lwAnnual, key = 's', label = 'Group') {"
assert s.count(ANCHOR) == 1
assert "credLadderCols" not in s

BLOCK = '''/**
 * The figures behind the pay-ladder chart.
 *
 * Every pay column here is pooled across the occupations at that credential and
 * weighted by their employment -- see pooledLadder() in lib/wage.js for why the
 * published ladder in percentiles.json will not do. "Times wider" is the p90
 * over the p10, which is the chart's spread stated as a number.
 */
export function credLadderCols(lwAnnual) {
  return [
    { k: 't', label: 'Entry credential', kind: 'text', get: (r) => r.t },
    { k: 'jobs', label: 'Jobs today', kind: 'num', get: (r) => r.jobs },
    { k: 'share', label: 'Share of all jobs', kind: 'pct', get: (r) => r.share },
    { k: 'p10', label: 'Lowest-paid tenth', kind: 'money', get: (r) => r.box.p10 },
    { k: 'p25', label: 'Lower quarter', kind: 'money', get: (r) => r.box.p25 },
    { k: 'p50', label: 'The midpoint job', kind: 'money', get: (r) => r.box.p50 },
    { k: 'p75', label: 'Upper quarter', kind: 'money', get: (r) => r.box.p75 },
    { k: 'p90', label: 'Highest-paid tenth', kind: 'money', get: (r) => r.box.p90 },
    {
      k: 'spread',
      label: 'Times wider',
      kind: 'x',
      get: (r) => (r.box.p10 ? r.box.p90 / r.box.p10 : null),
    },
    {
      k: 'lw',
      label: 'The midpoint against the benchmark',
      kind: 'x',
      get: (r) => (r.box.p50 ? r.box.p50 / lwAnnual : null),
    },
    { k: 'above', label: 'Clears the benchmark', kind: 'rate', get: (r) => r.above },
    { k: 'belowN', label: 'People below it', kind: 'num', get: (r) => r.belowN },
    { k: 'nocc', label: 'Occupations', kind: 'num', get: (r) => r.nocc },
  ];
}

'''
s = s.replace(ANCHOR, BLOCK + ANCHOR)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("tables.js patched,", len(s), "bytes")
