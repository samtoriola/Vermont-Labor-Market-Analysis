"""Two small chart additions for the Opportunities rebuild. Throwaway.

StackedRows was written for shares of a row's jobs: it normalises to r.total and
names every segment "Jobs" on hover. Pass total = 100 and it becomes an absolute
0-100 chart, which is what a score built from four percentile ranks needs -- but
the hover then lies about what it is showing. So the label and the formatter
become options, and the chart can carry an axis.

RankedBars gains a second figure column, as RangeRows already has, so a screen
can print openings, graduates and signals without any of the three moving into a
tooltip.
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


# ---- StackedRows: an axis, and honest segment labels ------------------------
sub("""  const names = opts.tierNames || [];
  const colors = opts.colors || SERIES;""",
    """  const names = opts.tierNames || [];
  const colors = opts.colors || SERIES;
  // What one segment IS. The default is this chart's first use -- a share of the
  // row's jobs -- but with total fixed and parts in the same units as the axis it
  // is an absolute chart, and then "Jobs" would be wrong.
  const partLabel = opts.partLabel || 'Jobs';
  const partFmt = opts.partFmt || fmt;""")

sub("""  const h = padT + rows.length * (rowH + gap) + 2;""",
    """  const ticks = opts.ticks || null;
  const padTop = ticks ? padT + 18 : padT;
  const h = padTop + rows.length * (rowH + gap) + 2;""")

sub("""      {opts.rightLabel ? (
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
        : null}""")

sub("""        const y = padT + i * (rowH + gap);""",
    """        const y = padTop + i * (rowH + gap);""")

sub("""              rows={[['Jobs', fmt(p.v)]]}
              meta={{
                big: [[share.toFixed(1) + '%', opts.shareLabel || 'Share of this row']],""",
    """              rows={p.extra || [[partLabel, partFmt(p.v)]]}
              meta={{
                big: [
                  [
                    opts.absolute ? partFmt(p.v) : share.toFixed(1) + '%',
                    opts.shareLabel || 'Share of this row',
                  ],
                ],""")

# ---- RankedBars: a second figure column -------------------------------------
sub("""  const hasRight = rows.some((r) => r.right !== undefined && r.right !== null);
  const padR = (opts.money ? 96 : 84) + (hasRight ? 58 : 0);""",
    """  const hasRight = rows.some((r) => r.right !== undefined && r.right !== null);
  const hasRight2 = rows.some((r) => r.right2 !== undefined && r.right2 !== null);
  const padR = (opts.money ? 96 : 84) + (hasRight ? 58 : 0) + (hasRight2 ? 58 : 0);""")

sub("""              {hasRight ? (
                <text
                  x={zeroX + max * scale + 67}
                  y={y + rowH / 2 + 4}
                  className="nbadge"
                  textAnchor="start"
                  fontSize={11.5}
                  opacity={dim ? 0.5 : 1}
                >
                  {r.right}
                </text>
              ) : null}""",
    """              {hasRight ? (
                <text
                  x={zeroX + max * scale + 67}
                  y={y + rowH / 2 + 4}
                  className="nbadge"
                  textAnchor="start"
                  fontSize={11.5}
                  opacity={dim ? 0.5 : 1}
                >
                  {r.right}
                </text>
              ) : null}
              {hasRight2 ? (
                <text
                  x={zeroX + max * scale + 125}
                  y={y + rowH / 2 + 4}
                  className="nbadge"
                  textAnchor="start"
                  fontSize={11.5}
                  opacity={dim ? 0.5 : 1}
                >
                  {r.right2}
                </text>
              ) : null}""")

sub("""      {hasRight && opts.rightHead ? (
        <text
          x={zeroX + max * scale + 67}
          y={padT - 30}
          className="nbadge"
          textAnchor="start"
          fontSize={9}
        >
          {opts.rightHead}
        </text>
      ) : null}""",
    """      {hasRight && opts.rightHead ? (
        <text
          x={zeroX + max * scale + 67}
          y={padT - 30}
          className="nbadge"
          textAnchor="start"
          fontSize={9}
        >
          {opts.rightHead}
        </text>
      ) : null}
      {hasRight2 && opts.rightHead2 ? (
        <text
          x={zeroX + max * scale + 125}
          y={padT - 30}
          className="nbadge"
          textAnchor="start"
          fontSize={9}
        >
          {opts.rightHead2}
        </text>
      ) : null}""")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("charts.js patched,", len(s), "bytes")
