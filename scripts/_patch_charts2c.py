"""Supplies the declarations the earlier patch dropped. Throwaway.

_patch_charts2.py mutated its string, hit a failing assertion on a later
substitution, and never reached its write -- so none of its work landed, while
_patch_charts2b.py went on to apply the uses of padTop, partLabel and partFmt.
charts.js has been referencing three undeclared names since. This declares them.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "components", "charts.js")
s = io.open(P, encoding="utf-8").read()
subs = [
    ("""  const names = opts.tierNames || [];
  const colors = opts.colors || SERIES;""",
     """  const names = opts.tierNames || [];
  const colors = opts.colors || SERIES;
  // What one segment IS. The default is this chart's first use -- a share of the
  // row's jobs -- but with the row total fixed and the parts in the same units as
  // the axis it is an absolute chart, and then "Jobs" would be wrong.
  const partLabel = opts.partLabel || 'Jobs';
  const partFmt = opts.partFmt || fmt;"""),
    ("""  const h = padT + rows.length * (rowH + gap) + 2;""",
     """  const ticks = opts.ticks || null;
  const padTop = ticks ? padT + 18 : padT;
  const h = padTop + rows.length * (rowH + gap) + 2;"""),
    ("""      {opts.rightLabel ? (
        <text x={w - padR + 9} y={padT - 3} className="nbadge" textAnchor="start" fontSize={9}>
          {opts.rightLabel}
        </text>
      ) : null}""",
     """      {opts.rightLabel ? (
        <text x={w - padR + 9} y={padTop - 3} className="nbadge" textAnchor="start" fontSize={9}>
          {opts.rightLabel}
        </text>
      ) : null}

      {/* Only where the row total is fixed. On a 100% chart every bar is the same
          length and an axis of shares would say nothing. */}
      {ticks
        ? ticks.map((tv) => {
            const gx = labW + (tv / (opts.axisMax || 100)) * plotW;
            return (
              <g key={`t${tv}`}>
                <line x1={gx} y1={padTop - 8} x2={gx} y2={h - 2} className="grid" strokeWidth={1} />
                <text x={gx} y={padTop - 14} className="nbadge" textAnchor="middle" fontSize={10}>
                  {tv}
                </text>
              </g>
            );
          })
        : null}"""),
]
# Check every substitution before writing any of them, which is the thing the
# earlier script got wrong.
for old, _ in subs:
    assert s.count(old) == 1, "%d occurrences of %r" % (s.count(old), old[:70])
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("charts.js repaired,", len(s), "bytes")
