"""Finishes the chart patches. Throwaway. (The `const y = padT + ...` line appears
in three charts, so the StackedRows one is matched with the line after it.)"""
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


sub("""        const y = padT + i * (rowH + gap);
        const tot = r.total || 1;""",
    """        const y = padTop + i * (rowH + gap);
        const tot = r.total || 1;""")

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
