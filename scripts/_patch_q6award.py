"""Degree type on VSCS alignment / Against demand.

sow.json now carries byAwardFamily: each occupation group's attributed graduates
split across the six award levels VSCS actually awards, summing to the same
1,700.0 the chart already divides by. So every place that says how many graduates
reach a group can now say what they graduated WITH.

Three places, deliberately not a fourth: the hover, the pinned detail pane, and
the table. Not the bar itself -- the bar's length is graduates as a share of the
openings that ask, and stacking a second dimension into it would make a reader
compare segment lengths across bars of different totals, which is the one thing a
share chart must not invite.

The award mix is the SAME allocation as the total beside it: modelled, not
observed. It inherits every caveat the total carries and adds none.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "components", "views", "Q6.js")
s = io.open(P, encoding="utf-8").read()

subs = [
    # ---- the helper -------------------------------------------------------
    ("""  const CRED_OPEN = credOpenByFamily();""",
     """  // Degree type, where the data has it. byAwardFamily drops anything under
  // 0.05 of a graduate, so a group can have a total with no mix behind it;
  // every caller treats that as "not broken down" rather than as zero.
  const AWARDS = V.awardOrder || [];
  const awardMix = (f) => (V.byAwardFamily || {})[f] || null;
  const awardRows = (f) => {
    const m = awardMix(f);
    return m ? AWARDS.filter((a) => m[a]).map((a) => [a, m[a].toFixed(1)]) : [];
  };

  const CRED_OPEN = credOpenByFamily();"""),

    # ---- the hover --------------------------------------------------------
    ("""                                  ['Graduates attributed', r.linked.toFixed(1)],
                                  ['Jobs', fmt(r.jobs)],
                                ],""",
     """                                  ['Graduates attributed', r.linked.toFixed(1)],
                                  ...awardRows(r.f),
                                  ['Jobs', fmt(r.jobs)],
                                ],"""),

    # ---- the table --------------------------------------------------------
    ("""                            { k: 'jobs', label: 'Jobs', kind: 'num', get: (r) => r.jobs },
                          ],""",
     """                            ...AWARDS.map((a) => ({
                              k: 'aw_' + a,
                              label: a,
                              kind: 'num1',
                              get: (r) => (awardMix(r.f) || {})[a] || null,
                            })),
                            { k: 'jobs', label: 'Jobs', kind: 'num', get: (r) => r.jobs },
                          ],"""),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("Q6.js: %d occurrences of %r" % (s.count(old), old[:70]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Q6.js patched, %d bytes" % len(s))
