"""Top 10 on Highest scoring, and makes the no-overlap claim in rank.js true.

The Show control offered Top 20 and Bottom 20 over a pool of 30, which is not two
ends of a ranking -- the two slices shared ten rows, and the comment in applyView
asserted they could not. Nothing read wrong on screen, which is why it survived:
both views drew twenty plausible bars.

So `show` is honoured only where it actually partitions the pool, and the two
charts that set it take round numbers: 10 of 30 scored occupations, 20 of the
49 clearing the screen. Where a tightened screen leaves too few rows for its
slice, the control falls back to halves, which is what it does on every chart
that does not set `show`. Throwaway.
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


edit("lib/rank.js", [
    ("""/**
 * The views available for a list of `n` rows.""",
     """/**
 * The slice size `show` asks for, where the pool can actually give it.
 *
 * Two views of a ranking have to be two ENDS of it. `show` of 20 over a pool of
 * 30 is not: the top twenty and the bottom twenty share ten rows, and a reader
 * switching between them sees a third of the chart stay put. Where the pool
 * cannot give both slices, the request is dropped and the halves take over.
 */
function sliced(n, show) {
  return show && show < n && show * 2 <= n ? show : null;
}

/**
 * The views available for a list of `n` rows."""),
    ("""  if (show && show < n) {
    const views = [
      { id: 'top', label: `Top ${show}`, n: show },
      { id: 'bottom', label: `Bottom ${show}`, n: show },
    ];
    if (n <= ALL_MAX) views.push({ id: 'all', label: `All ${n}`, n });
    return views;
  }""",
     """  const s = sliced(n, show);
  if (s) {
    const views = [
      { id: 'top', label: `Top ${s}`, n: s },
      { id: 'bottom', label: `Bottom ${s}`, n: s },
    ];
    if (n <= ALL_MAX) views.push({ id: 'all', label: `All ${n}`, n });
    return views;
  }"""),
    ("""  const n = rows.length;
  const top = show && show < n ? show : topSlice(n);
  if (view === 'top') return rows.slice(0, top);""",
     """  const n = rows.length;
  const s = sliced(n, show);
  const top = s || topSlice(n);
  if (view === 'top') return rows.slice(0, top);"""),
    ("""  const size = show && show < n ? show : n - top;""",
     """  const size = s || n - top;"""),
    ("""  // Where the pool splits, the bottom is whatever the top leaves -- which is
  // more than half, because topSlice rounds the top down to a round number. The
  // two have to partition the pool, not share a row between them. Where `show`
  // is set both views are that size by definition and cannot overlap.""",
     """  // Where the pool splits, the bottom is whatever the top leaves -- which is
  // more than half, because topSlice rounds the top down to a round number. The
  // two have to partition the pool, not share a row between them, which is what
  // sliced() is checking before it honours `show`."""),
])

edit("components/views/Q5.js", [
    ("""<Ranked id="q5-score" rows={shown} show={20}>""",
     """<Ranked id="q5-score" rows={shown} show={10}>"""),
    ("""<Ranked id="q5-screen" rows={screened} show={16}>""",
     """<Ranked id="q5-screen" rows={screened} show={20}>"""),
])
