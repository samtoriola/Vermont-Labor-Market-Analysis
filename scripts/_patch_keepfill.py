"""keepFill for StackedRows, and switched on for both Opportunities charts.

Choosing a bar fades the rest to 32%, which reads well when colour is only a
category. On both of these charts colour is a measure -- four percentile ranks on
one, the VSCS pipeline on the other -- and fading it washes the second variable
out of the chart the moment anyone clicks anything. RankedBars already had
keepFill for exactly this; StackedRows did not. Throwaway.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))


def edit(rel, pairs):
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _ in pairs:
        assert s.count(old) == 1, "%s: %d occurrences of %r" % (rel, s.count(old), old[:70])
    for old, new in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(rel, "patched,", len(s), "bytes")


edit("components/charts.js", [
    ("""              <rect
                x={x}
                y={y}
                width={Math.max(0.5, pw - 2)}
                height={rowH}
                rx={2}
                fill={V(colors[k])}
                fillOpacity={dim ? 0.32 : 1}
              />""",
     """              {/* Where the segment colours are a measure rather than a set of
                   categories, fading them destroys what the chart is saying. The
                   labels fade instead, and the chosen row takes an outline. */}
              <rect
                x={x}
                y={y}
                width={Math.max(0.5, pw - 2)}
                height={rowH}
                rx={2}
                fill={V(colors[k])}
                fillOpacity={dim && !opts.keepFill ? 0.32 : 1}
              />"""),
    ("""            {segs}
            {r.hi !== undefined ? (""",
     """            {segs}
            {r.active && opts.keepFill ? (
              <rect
                x={labW}
                y={y}
                width={Math.max(1, x - labW)}
                height={rowH}
                rx={2}
                fill="none"
                stroke={V('--ink')}
                strokeWidth={1.5}
                pointerEvents="none"
              />
            ) : null}
            {r.hi !== undefined ? ("""),
])

edit("components/views/Q5.js", [
    ("""                                    rightLabel: 'SCORE',
                                    hiFmt: (v) => v,""",
     """                                    rightLabel: 'SCORE',
                                    hiFmt: (v) => v,
                                    // The segments are the measure here.
                                    keepFill: true,"""),
    ("""                            width,
                            labelWidth: 290,
                            valueLabel: 'Openings a year',""",
     """                            width,
                            labelWidth: 290,
                            // The bar's shade is the pipeline, so choosing one must
                            // not fade the other fifteen into one colour.
                            keepFill: true,
                            valueLabel: 'Openings a year',"""),
])
