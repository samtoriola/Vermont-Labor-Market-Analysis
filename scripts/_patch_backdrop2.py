"""Moves the row backdrop inside the clickable mark. Throwaway.

Drawn outside TipMark it sat over the bar's own group, so a click anywhere past
the end of the filled part hit the backdrop and did nothing -- which Playwright
found by aiming at the centre of the mark's bounding box. On this chart the
backdrop IS the row, so it belongs inside the mark: the whole row then hovers and
clicks as one thing, which is also how it reads.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "components", "charts.js")
s = io.open(P, encoding="utf-8").read()

OLD = """            {/* A backdrop belonging to this row rather than to the scale: the bar
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
            ) : null}
"""
assert s.count(OLD) == 1
s = s.replace(OLD, "")

ANCHOR = """              <rect
                x={bx}
                y={y}
                width={bw}
                height={rowH}
                rx={4}
                fill={V(r.color || '--s1')}"""
NEW = """              {/* A backdrop belonging to this row rather than to the scale: the
                  bar is a part of it, and the gap between the two is the measure.
                  Inside the mark, so the whole row hovers and clicks as one
                  thing -- outside it, it covered the bar and swallowed the
                  click. */}
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
              ) : null}
""" + ANCHOR
assert s.count(ANCHOR) == 1
s = s.replace(ANCHOR, NEW)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("charts.js patched,", len(s), "bytes")
