"""Adds a per-row backdrop to RankedBars. Throwaway.

opts.track draws the axis maximum behind every bar, for a 0-100% chart where the
remainder of the SCALE is the answer. A nested bar is a different thing: the
remainder of THAT ROW is the answer -- a year's openings at one credential, with
the part of them in work that pays filled in -- so the backdrop is a per-row
value, not a constant.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "components", "charts.js")
s = io.open(P, encoding="utf-8").read()


def sub(old, new):
    global s
    assert s.count(old) == 1, "%d occurrences of %r" % (s.count(old), old[:70])
    s = s.replace(old, new)


# The axis has to clear the backdrops, not only the bars, or a nested bar would
# run past the end of the plot.
sub("""  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.value)));""",
    """  const maxAbs = Math.max(
    ...rows.map((r) => Math.max(Math.abs(r.value), Math.abs(r.backdrop || 0)))
  );""")

sub("""            {opts.track ? (
              <rect
                x={zeroX}
                y={y}
                width={max * scale}
                height={rowH}
                rx={4}
                fill={V('--track')}
                opacity={dim ? 0.5 : 1}
              />
            ) : null}""",
    """            {opts.track ? (
              <rect
                x={zeroX}
                y={y}
                width={max * scale}
                height={rowH}
                rx={4}
                fill={V('--track')}
                opacity={dim ? 0.5 : 1}
              />
            ) : null}
            {/* A backdrop belonging to this row rather than to the scale: the bar
                is a part of it, and the gap between the two is the measure. */}
            {r.backdrop ? (
              <rect
                x={zeroX}
                y={y}
                width={Math.max(1.5, r.backdrop * scale)}
                height={rowH}
                rx={4}
                fill={V('--track')}
                opacity={dim ? 0.5 : 1}
              />
            ) : null}""")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("charts.js patched,", len(s), "bytes")
