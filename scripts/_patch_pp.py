"""Percentage points are not percent.

"Projected vs observed" subtracts one growth rate from another, so its unit is
percentage points, not percent. The caption said so; the bar labels, the axis
ticks and the hover headline all said "%", which is the reading that actually
reaches a presenter. Farming reads +14.0 there -- +7.8 projected minus -6.2
observed -- and "+14.0%" invites someone to say farming is growing 14 percent,
which is the opposite of what the bar means: that group SHRANK.

A `pp` mode on fmtVal and a `pp` kind on the table, rather than a one-off string
in Q3, because the same subtraction happens elsewhere: County living wage's
"Difference" column is one share minus another and carried the same wrong unit.

Axis decimals are left alone. tickDec: 0 would read better here (-16 pp, -8 pp)
but niceMax can return a 3.0 or 7.5 top on a narrower slice, whose quarters are
1.5s; rounding those to whole numbers would print two ticks with the same label.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

EDITS = [
    # ------------------------------------------------------------ format.js --
    ("../lib/format.js", [(
        """  if (o.mode === 'pct') {
    const d = o.dec === undefined ? 1 : o.dec;
    return (o.signed && v > 0 ? '+' : '') + v.toFixed(d) + '%';
  }""",
        """  if (o.mode === 'pct') {
    const d = o.dec === undefined ? 1 : o.dec;
    return (o.signed && v > 0 ? '+' : '') + v.toFixed(d) + '%';
  }
  // Percentage POINTS: one rate minus another. A reader who sees "%" on the
  // difference between two percentages will read it as a rate, which is how
  // "+7.8% projected, -6.2% observed" turns into "growing 14%" out loud.
  if (o.mode === 'pp') {
    const d = o.dec === undefined ? 1 : o.dec;
    return (o.signed && v > 0 ? '+' : '') + v.toFixed(d) + ' pp';
  }""")]),

    # --------------------------------------------------------- DataTable.js --
    ("../components/DataTable.js", [
        ("""    case 'pct':
      return (v > 0 ? '+' : '') + v.toFixed(1) + '%';""",
         """    case 'pct':
      return (v > 0 ? '+' : '') + v.toFixed(1) + '%';
    // One rate minus another. Signed like pct and coloured like pct, but the
    // unit is points, and saying so is the whole reason the kind exists.
    case 'pp':
      return (v > 0 ? '+' : '') + v.toFixed(1) + ' pp';"""),

        ("""  if (kind === 'pct' && typeof v === 'number') {""",
         """  if ((kind === 'pct' || kind === 'pp') && typeof v === 'number') {"""),

        ("""/** pct cells carry direction in color as well as sign. */""",
         """/** pct and pp cells carry direction in color as well as sign. */"""),
    ]),

    # ------------------------------------------------------------ tables.js --
    ("../lib/tables.js", [
        ("""    { k: 'g5pct', label: 'Projected by 2030', kind: 'pct', get: (r) => r.g5pct },
    { k: 'med', label: 'Median pay', kind: 'money', get: (r) => r.med },""",
         """    { k: 'g5pct', label: 'Projected by 2030', kind: 'pct', get: (r) => r.g5pct },
    // The fourth measure's own number. The two columns above it are its inputs,
    // and a reader checking the chart should not have to subtract them by hand
    // -- which is also the subtraction that makes the unit points, not percent.
    {
      k: 'gap',
      label: 'Projected minus observed',
      kind: 'pp',
      get: (r) => (r.g5pct === null || r.chgPct === null ? null : r.g5pct - r.chgPct),
    },
    { k: 'med', label: 'Median pay', kind: 'money', get: (r) => r.med },"""),

        ("""    { k: 'd', label: 'Difference', kind: 'pct', get: (r) => r.local - r.state },""",
         """    // One share minus another, so points rather than percent.
    { k: 'd', label: 'Difference', kind: 'pp', get: (r) => r.local - r.state },"""),
    ]),

    # ---------------------------------------------------------------- Q3.js --
    ("../components/views/Q3.js", [
        ("""                value: r.gap,
                color: r.gap >= 0 ? '--good' : '--bad',
                mode: 'pct',""",
         """                value: r.gap,
                color: r.gap >= 0 ? '--good' : '--bad',
                mode: 'pp',"""),

        ("""                mode: 'pct',
                signed: true,
                valueLabel: 'Projection minus what happened',""",
         """                mode: 'pp',
                signed: true,
                valueLabel: 'Projection minus what happened',"""),

    ]),
]

for rel, subs in EDITS:
    p = os.path.join(H, rel)
    s = io.open(p, encoding="utf-8").read()
    for old, new in subs:
        if s.count(old) != 1:
            raise SystemExit("%s: %d occurrences of %r" % (rel, s.count(old), old[:70]))

for rel, subs in EDITS:
    p = os.path.join(H, rel)
    s = io.open(p, encoding="utf-8").read()
    for old, new in subs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("patched %s" % rel)
