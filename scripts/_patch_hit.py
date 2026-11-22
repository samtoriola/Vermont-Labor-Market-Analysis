"""Gives a RankedBars row a hit area across the plot. Throwaway.

Where the value label sits in a fixed column -- any chart with a track, a backdrop
or a second figure column -- a row's mark spans from the bar's start to that
column, and most of that span is empty. A click aimed at the middle of the mark
lands on the svg and does nothing, which is what a reader aiming at the row does
too. RangeRows already carries a transparent band for this reason; this gives the
same thing to the charts that need it.

Not added to plain ranked bars: there the label sits at the bar's own tip, so the
mark is already the width of what is drawn, and a band would make hovering the
empty right-hand side of a short row pop up a tooltip for no reason.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "components", "charts.js")
s = io.open(P, encoding="utf-8").read()

OLD = """              {/* A backdrop belonging to this row rather than to the scale: the
                  bar is a part of it, and the gap between the two is the measure.
                  Inside the mark, so the whole row hovers and clicks as one
                  thing -- outside it, it covered the bar and swallowed the
                  click. */}"""
NEW = """              {/* Where the value sits in a fixed column, the drawn bar is only
                  part of the row the reader is aiming at. A transparent band makes
                  the rest of it hit, rather than leaving a dead zone between the
                  bar's end and its figure. */}
              {opts.track || hasRight || r.backdrop ? (
                <rect x={zeroX} y={y} width={max * scale} height={rowH} fill="transparent" />
              ) : null}
              {/* A backdrop belonging to this row rather than to the scale: the
                  bar is a part of it, and the gap between the two is the measure.
                  Inside the mark, so the whole row hovers and clicks as one
                  thing -- outside it, it covered the bar and swallowed the
                  click. */}"""
assert s.count(OLD) == 1
s = s.replace(OLD, NEW)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("charts.js patched,", len(s), "bytes")
