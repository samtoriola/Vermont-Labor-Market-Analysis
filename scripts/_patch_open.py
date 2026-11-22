"""The read-out and the two column sets the openings section needs. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))


def patch(rel, anchor, block, after=False):
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    assert s.count(anchor) == 1, "%s: %d occurrences" % (rel, s.count(anchor))
    s = s.replace(anchor, (anchor + block) if after else (block + anchor))
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(rel, "patched,", len(s), "bytes")


# ---- the read-out ----------------------------------------------------------
patch("lib/insight.js", "/* ---------- what postings ask for ---------- */", '''/**
 * A year's hiring at each credential, against the benchmark.
 *
 * Reads the two ends of the ladder rather than the widest gap: the ordering here
 * is monotonic by construction -- higher credentials pay better -- so naming the
 * biggest step would say the same thing every time. What is worth saying is the
 * size of the gap and how much hiring sits at the bottom of it.
 */
export function openingsSplit(rows, minGap = 15) {
  const v = rows.filter((r) => r.openAll > 0);
  if (v.length < 2) return null;
  const s = v.slice().sort((a, b) => a.share - b.share);
  const lo = s[0];
  const hi = s[s.length - 1];
  if (hi.share - lo.share < minGap) {
    return none('A year of hiring clears the benchmark at a similar rate across credentials.');
  }
  const shortfall = v.reduce((a, r) => a + (r.openAll - r.openPay), 0);
  return found(
    `${lo.share.toFixed(0)}% of a year's openings at ${shortName(lo.t).toLowerCase()} are in ` +
    `work paying a living wage, against ${hi.share.toFixed(0)}% at ` +
    `${shortName(hi.t).toLowerCase()}. Across every credential that leaves ` +
    `${fmt(shortfall)} of ${fmt(v.reduce((a, r) => a + r.openAll, 0))} openings a year in ` +
    `work that does not pay one.`
  );
}

''')

# ---- the figures behind the chart ------------------------------------------
patch("lib/tables.js", "export function bandCols(lwAnnual, key = 's', label = 'Group') {", '''/**
 * A year's openings at each entry credential, split by the benchmark.
 *
 * "In work that pays" is weighted by each occupation's own pay distribution, so
 * an occupation whose midpoint clears the benchmark by a dollar contributes about
 * half its openings rather than all of them. See rollUpOn() in lib/wage.js.
 */
export function openingsCols() {
  return [
    { k: 't', label: 'Entry credential', kind: 'text', get: (r) => r.t },
    { k: 'openAll', label: 'Openings a year', kind: 'num', get: (r) => r.openAll },
    { k: 'openPay', label: 'In work that pays a living wage', kind: 'num', get: (r) => r.openPay },
    { k: 'share', label: 'Share of its openings', kind: 'rate', get: (r) => r.share },
    { k: 'openShort', label: 'In work that does not', kind: 'num', get: (r) => r.openAll - r.openPay },
    { k: 'nocc', label: 'Occupations', kind: 'num', get: (r) => r.nocc },
    { k: 'nDoor', label: 'Hiring 50+ a year and paying', kind: 'num', get: (r) => r.nPaying },
  ];
}

''')

# ---- the drill's columns ---------------------------------------------------
patch("components/occCols.js", """/** Master table also names the family and SOC, which the drill-down already implies. */""", '''/**
 * The drill behind the openings chart.
 *
 * Leads with openings rather than with jobs, because that is what the chart above
 * it counts, and carries the two measures the chart is built from: how much of
 * each occupation pays below the benchmark, and what that leaves of its openings.
 */
export function occOpenCols(lwAnnual) {
  const below = (o) => shareBelow(occBox(o), lwAnnual);
  return [
    { k: 'n', label: 'Occupation', kind: 'text', get: (o) => o.n },
    { k: 'o', label: 'Openings a year', kind: 'num', get: (o) => o.o },
    { k: 'm', label: 'Typical pay', kind: 'money', get: (o) => o.m },
    { k: 'lw', label: 'Times the living wage', kind: 'x', get: (o) => (o.m ? o.m / lwAnnual : null) },
    { k: 'below', label: 'Share of its jobs below the benchmark', kind: 'rate', get: below },
    {
      k: 'openPay',
      label: 'Openings in work that pays',
      kind: 'num',
      get: (o) => {
        const b = below(o);
        return b === null || !o.o ? null : (o.o * (100 - b)) / 100;
      },
    },
    { k: 'j', label: 'Jobs today', kind: 'num', get: (o) => o.j },
    { k: 'turn', label: 'Turnover', kind: 'rate', get: (o) => o.turn },
    { k: 't', label: 'Entry credential', kind: 'text', get: (o) => o.t },
  ];
}

''')

# imports those two column sets need
for rel, old, new in [
    ("lib/insight.js",
     "import { shortLabel } from './labels';",
     "import { shortLabel } from './labels';\nconst shortName = shortLabel;"),
    ("components/occCols.js",
     "import { TOTJ } from '@/lib/data';",
     "import { TOTJ } from '@/lib/data';\nimport { shareBelow, occBox } from '@/lib/wage';"),
]:
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    if new.split("\n")[-1] in s:
        print(rel, "import already present")
        continue
    assert s.count(old) == 1, rel
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))
    print(rel, "import added")
