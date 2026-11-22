""""People below" counts jobs, so it says Jobs below.

belowN is a jobs-weighted sum -- each occupation's jobs times the share of them
paying under the benchmark -- so someone holding two jobs is in it twice. Methods'
"Jobs vs workers" rule says every chart that ranks or compares work counts jobs,
and this was the one measure on screen whose label said otherwise. It read as the
headcount of underpaid Vermonters, which is a number the dashboard does not have.

The arithmetic is untouched; only what it is called.

Checks every substitution before writing anything.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
EDITS = []


def edit(rel, pairs):
    EDITS.append((rel, pairs))


# ------------------------------------------------------------------- Q2.js ---
edit("components/views/Q2.js", [
    ("""// Share and headcount give different answers over the same rows, and the gap
// between them is the reason to carry both: the work least likely to pay a living
// wage is not where most of the people paid under one actually are.
const MEASURES = [
  { id: 'share', label: 'Share of jobs below' },
  { id: 'count', label: 'People below' },
];""",
     """// Share and headcount give different answers over the same rows, and the gap
// between them is the reason to carry both: the work least likely to pay a living
// wage is not where most of the underpaid work actually is.
//
// Both count JOBS. The headcount is each occupation's jobs times the share of them
// under the benchmark, so a person holding two jobs is in it twice -- it is not a
// count of underpaid Vermonters, which is a figure this data cannot give.
const MEASURES = [
  { id: 'share', label: 'Share of jobs below' },
  { id: 'count', label: 'Jobs below' },
];"""),
    ("""            measure === 'share' ? 'People below it' : 'Share of its jobs',""",
     """            measure === 'share' ? 'Jobs below it' : 'Share of its jobs',"""),
    ("""            ? [['Most people short', `${r.worst.o.n} (${fmt(Math.round(r.worst.n))})`]]""",
     """            ? [['Most jobs short', `${r.worst.o.n} (${fmt(Math.round(r.worst.n))})`]]"""),
    ("""                                : 'How many people are in work that pays below a living wage?'""",
     """                                : 'How many jobs pay below a living wage?'"""),
    ("""                                  measure === 'share' ? 'Below the benchmark' : 'People below',""",
     """                                  measure === 'share' ? 'Below the benchmark' : 'Jobs below',"""),
    ("""                                    : 'People in jobs paying below the living wage'""",
     """                                    : 'Jobs paying below the living wage'"""),
])

# ------------------------------------------------------------- Overview.js ---
edit("components/views/Overview.js", [
    ("        [fmt(r.belowN), 'People short'],", "        [fmt(r.belowN), 'Jobs short'],"),
    ("      ['People below it', fmt(r.belowN)],", "      ['Jobs below it', fmt(r.belowN)],"),
    ("""        ? [['Most people short', `${r.worst.o.n} (${fmt(Math.round(r.worst.n))})`]]""",
     """        ? [['Most jobs short', `${r.worst.o.n} (${fmt(Math.round(r.worst.n))})`]]"""),
    ("""            { k: 'belowN', label: 'People below it', kind: 'num', get: (r) => r.belowN },""",
     """            { k: 'belowN', label: 'Jobs below it', kind: 'num', get: (r) => r.belowN },"""),
])

# ------------------------------------------------------------------- Q4.js ---
edit("components/views/Q4.js", [
    ("                    ['People below it', fmt(r.belowN)],",
     "                    ['Jobs below it', fmt(r.belowN)],"),
])

# --------------------------------------------------------------- tables.js ---
edit("lib/tables.js", [
    ("{ k: 'belowN', label: 'People below it', kind: 'num', get: (r) => r.belowN },",
     "{ k: 'belowN', label: 'Jobs below it', kind: 'num', get: (r) => r.belowN },"),
])

# -------------------------------------------------------------- insight.js ---
edit("lib/insight.js", [
    (""" * Share and headcount give different answers and the gap between them is the
 * finding: Healthcare Support has the highest share of jobs below the benchmark,
 * but the most people below are in Food Preparation, which is twice its size at a
 * lower rate.""",
     """ * Share and headcount give different answers and the gap between them is the
 * finding: Healthcare Support has the highest share of jobs below the benchmark,
 * but the most jobs below are in Food Preparation, which is twice its size at a
 * lower rate. Both count jobs -- the headcount is the share times employment, not
 * a count of people."""),
    ("""      `${name(byShare)} is both the ${label} least likely to pay a living wage and the ` +
      `one with the most people in it who are paid less — ${byShare.below.toFixed(0)}% of ` +
      `its ${fmt(byShare.jobs)} jobs, ${fmt(byShare.belowN)} people.`""",
     """      `${name(byShare)} is both the ${label} least likely to pay a living wage and the ` +
      `one holding the most jobs that pay less — ${byShare.below.toFixed(0)}% of ` +
      `its ${fmt(byShare.jobs)} jobs, ${fmt(byShare.belowN)} of them.`"""),
    ("""        `${name(byCount)} holds the most people paid under the benchmark — ` +""",
     """        `${name(byCount)} holds the most jobs paid under the benchmark — ` +"""),
    ("""        `${byShare.below.toFixed(0)}% of its ${fmt(byShare.jobs)} jobs fall short. But the most ` +
        `people short are in ${name(byCount)} — ${fmt(byCount.belowN)} of them. Switch the measure.`""",
     """        `${byShare.below.toFixed(0)}% of its ${fmt(byShare.jobs)} jobs fall short. But the most ` +
        `jobs short are in ${name(byCount)} — ${fmt(byCount.belowN)} of them. Switch the measure.`"""),
    ("""  // short[0] is the biggest of the underpaid groups and `worst` holds the most
  // people under the benchmark. They are usually the same group, and naming it
  // twice in one sentence reads as a mistake rather than as two findings.""",
     """  // short[0] is the biggest of the underpaid groups and `worst` holds the most
  // jobs under the benchmark. They are usually the same group, and naming it
  // twice in one sentence reads as a mistake rather than as two findings."""),
    ("""      : `The most people short are in ${shortName(worst.f)}, ${fmt(worst.belowN)} of them.`;""",
     """      : `The most jobs short are in ${shortName(worst.f)}, ${fmt(worst.belowN)} of them.`;"""),
])

# -------------------------------------------------------------- the test ----
edit("scripts/e2e_wage.py", [
    ('    chip(pg, "Measure", "People below")', '    chip(pg, "Measure", "Jobs below")'),
])

# ------------------------------------------------------------------ apply ---
loaded = []
for rel, pairs in EDITS:
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _ in pairs:
        want = 2 if rel == "lib/tables.js" else 1
        if s.count(old) != want:
            raise SystemExit("%s: %d occurrences of %r" % (rel, s.count(old), old[:90]))
    loaded.append((p, rel, s, pairs))

for p, rel, s, pairs in loaded:
    for old, new in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("%-32s %d edits, %d bytes" % (rel, len(pairs), len(s)))
