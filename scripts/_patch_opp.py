"""Review 11/18, Opportunity: the component is replacement, not advertising.

Ranked so that LOW replacement scores HIGH -- a lower share of the workforce
leaving each year being the better position. scripts/rebuild_opp.py does the
arithmetic and prints the correlation matrix; this carries the new component
through everything that names the old one.

THE CAVEAT, recorded on Methods because a reader of the index deserves it:
postings against pay ranked r = +0.394. Replacement against pay ranks r = +0.611,
because Vermont's high-replacement work is its low-paid work and inverting the
sign flips that relationship rather than removing it. The pay dimension now has
something close to one and a half votes out of four. The index is still the mean
of four ranks, and the panel still shows every one of them, so the reader can see
it; but it is less independent than it was.

Also adds the "rank by" control the review asks for: the same 406 occupations
ordered by any single component instead of by the composite, which is the
cheapest honest answer to "a way to view wages, growth".
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

EDITS = {
    "components/views/Q5.js": [
        ("{ k: 's_postings', label: 'Advertising', color: '--ord2' },",
         "{ k: 's_replacement', label: 'Stability', color: '--ord2' },", 1),
        ("""      ['Advertising', r.s_postings, r.pp + ' ads per 100'],""",
         """      ['Stability', r.s_replacement, r.turn + '% replaced a year'],""", 1),
        ("""   * The ramp skips --ord3: four segments from one hue need the contrast between
   * neighbours more than they need even spacing.
   */""",
         """   * The ramp skips --ord3: four segments from one hue need the contrast between
   * neighbours more than they need even spacing.
   *
   * STABILITY, not advertising. The 11/18 review swapped the postings component
   * for the replacement rate, inverted: an occupation that replaces less of its
   * workforce each year scores higher. Worth knowing when reading the bar that
   * this component ranks r = +0.611 against pay, where postings ranked +0.394 --
   * low-replacement work is well-paid work in Vermont, so the pay dimension is
   * carrying more of this score than a quarter of it. Methods says so too.
   */""", 1),
    ],
    "lib/tables.js": [
        ("{ k: 's_postings', label: 'Score: job ads', kind: 'num1', get: (r) => r.s_postings },",
         "{ k: 's_replacement', label: 'Score: stability', kind: 'num1', get: (r) => r.s_replacement },", 1),
    ],
    "scripts/build_workfiles.py": [
        ('r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"],',
         'r["s_size"], r["s_growth"], r["s_replacement"], r["s_pay"],', 1),
        ('n1((r["s_size"] + r["s_growth"] + r["s_postings"] + r["s_pay"]) / 4),',
         'n1((r["s_size"] + r["s_growth"] + r["s_replacement"] + r["s_pay"]) / 4),', 1),
        ('      max(r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"])\n'
         '      - min(r["s_size"], r["s_growth"], r["s_postings"], r["s_pay"])]',
         '      max(r["s_size"], r["s_growth"], r["s_replacement"], r["s_pay"])\n'
         '      - min(r["s_size"], r["s_growth"], r["s_replacement"], r["s_pay"])]', 1),
    ],
    # So a future full rebuild agrees with what is committed.
    "scripts/build_sow.py": [
        ("""COMPS = [("size", "jobs"), ("growth", "g5pct"),
         ("postings", "postPer100"), ("pay", "med")]""",
         """# 11/18 review: replacement, inverted, in place of postings intensity. Low
# replacement ranks high. See scripts/rebuild_opp.py, which did this against the
# committed data and prints the correlation matrix -- replacement ranks r=+0.611
# against pay where postings ranked +0.394, so this component is less independent
# than the one it displaced. Kept because the review asked for it and stability is
# a defensible signal, but it is not a free swap.
elig["negTurn"] = -elig["turnRate"]
COMPS = [("size", "jobs"), ("growth", "g5pct"),
         ("replacement", "negTurn"), ("pay", "med")]""", 1),
    ],
}

loaded = []
for rel, pairs in EDITS.items():
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _, want in pairs:
        if s.count(old) != want:
            raise SystemExit("%s: %d of %r, expected %d" % (rel, s.count(old), old[:60], want))
    loaded.append((p, rel, s, pairs))

for p, rel, s, pairs in loaded:
    for old, new, _ in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("%-32s patched" % rel)
