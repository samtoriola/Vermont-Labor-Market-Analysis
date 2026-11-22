"""Review 11/18, Demand & growth.

GENERAL DEMAND: the postings-per-job figure comes off the bottom of the columns.
It was a guard against reading column height as demand, but the columns each sum
to 100% and do not encode height at all, so the guard was answering a misreading
the chart had already prevented -- at the cost of a second number under every
column in a chart whose whole point is the four-way split above it. The figure
stays in the table under the chart, where demandCols already carries it.

HIRING AND GROWTH gains three things:
  - a fourth measure, projected growth set against what actually happened since
    2021. Both were already on the control as separate rankings, and the review
    wants the difference, which is a third quantity neither chart shows: a group
    can be projected to grow and still be projected to grow more slowly than it
    just did. Coloured by sign, because this one genuinely contrasts two sides.
  - click-through on all four, opening the occupations inside a group. The drill
    carries typical entry education, which is the column the review asked for.
  - the living-wage benchmark, which the drill prices its occupations against. It
    is on this section and not on General demand: postings education and
    experience have nothing to do with a pay floor, and a control that changes
    nothing is worse than no control.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "components", "views", "Q3.js")
s = io.open(P, encoding="utf-8").read()

subs = [
    # ------------------------------------------------------------ imports --
    ("import { DATA, DEMAND, LC, ORDINAL, TOTJ } from '@/lib/data';",
     "import { DATA, DEMAND, LC, ORDINAL, TOTJ, lwAnnual, occByFamily } from '@/lib/data';"),

    ("import { Callout, HowTo, Panel, Legend, Picker, Ranked, Scope, VHead, N } from '../ui';",
     "import { Callout, HowTo, LwPicker, Panel, Legend, Picker, Ranked, Scope, VHead, N } from '../ui';\n"
     "import { useDrill, occDrill } from '../Drill';"),

    # ------------------------------------------------------- the measures --
    ("""const DEMAND_MEASURES = [
  { id: 'ads', label: 'Job ads' },
  { id: 'observed', label: 'Change since 2021' },
  { id: 'projected', label: 'Projected growth' },
];""",
     """const DEMAND_MEASURES = [
  { id: 'ads', label: 'Job ads' },
  { id: 'observed', label: 'Change since 2021' },
  { id: 'projected', label: 'Projected growth' },
  { id: 'momentum', label: 'Projected vs observed' },
];"""),

    # ------------------------------------------------------- the signature --
    ("""export default function Q3({ section }) {
  const fams = LC.families.slice();""",
     """export default function Q3({ lw, setLw, section }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();
  const fams = LC.families.slice();

  // Every ranking on this section is one bar per occupation group, so every one
  // of them can open the same way: the occupations inside it, priced against the
  // benchmark, with their typical entry education beside them.
  const famDrill = (f) =>
    open(
      occDrill({
        label: 'Occupation group',
        title: f,
        cap: 'Every occupation in this group, largest first.',
        occ: occByFamily(f),
        lwAnnual: LWA,
      })
    );"""),

    # ---------------------------------------------- click-through on bars --
    ("""                label: r.f,
                value: r.idx,
                color: r.idx >= 1 ? '--s3' : '--s2',
                dec: 2,""",
     """                label: r.f,
                value: r.idx,
                color: r.idx >= 1 ? '--s3' : '--s2',
                dec: 2,
                onClick: () => famDrill(r.f),"""),

    ("""                label: r.f,
                value: r.chgPct,
                color: r.chgPct >= 0 ? '--s3' : '--s2',
                mode: 'pct',""",
     """                label: r.f,
                value: r.chgPct,
                color: r.chgPct >= 0 ? '--s3' : '--s2',
                mode: 'pct',
                onClick: () => famDrill(r.f),"""),

    ("""                label: r.f,
                value: r.g5pct,
                color: r.g5pct >= 0 ? '--s3' : '--s2',
                mode: 'pct',""",
     """                label: r.f,
                value: r.g5pct,
                color: r.g5pct >= 0 ? '--s3' : '--s2',
                mode: 'pct',
                onClick: () => famDrill(r.f),"""),

    ("""                valueLabel: 'Ads per job, vs its size',
                aria: 'Postings alignment index',""",
     """                valueLabel: 'Ads per job, vs its size',
                clickHint: 'Click for the occupations inside it',
                aria: 'Postings alignment index',"""),

    ("""                valueLabel: 'Change since 2021',
                aria: 'Observed change 2021 to 2025 by occupation group',""",
     """                valueLabel: 'Change since 2021',
                clickHint: 'Click for the occupations inside it',
                aria: 'Observed change 2021 to 2025 by occupation group',"""),

    ("""                valueLabel: 'Growth by 2030',
                aria: 'Projected five-year growth by occupation group',""",
     """                valueLabel: 'Growth by 2030',
                clickHint: 'Click for the occupations inside it',
                aria: 'Projected five-year growth by occupation group',"""),

    # ------------------------------------------- the fourth measure ---------
    ("""        </Ranked>
      ),
    },
  };

  // ---- what postings ask for ---------------------------------------------""",
     """        </Ranked>
      ),
    },

    // Projection against recent history. Both halves were already on this
    // control as rankings of their own, and the quantity the review is after is
    // in neither: whether the next five years are expected to go faster or
    // slower than the last four did. A group can be projected to grow and still
    // be projected to lose pace.
    //
    // Signed, so the semantic pair is doing what it is reserved for -- two sides
    // of a line inside one chart -- rather than shading a magnitude.
    momentum: {
      title: 'Is the projection faster or slower than what already happened?',
      cap:
        'Projected five-year growth minus the change already observed between 2021 and ' +
        '2025, in percentage points. To the right is a group expected to pick up pace; to ' +
        'the left, one expected to grow more slowly than it just did — which includes ' +
        'groups that are still growing.',
      src: 'Vermont occupation data · 2030 projection against 2025 jobs, and 2025 against 2021',
      table: 'projected-against-observed',
      sort: { k: 'g5pct', dir: -1 },
      chart: (
        <Ranked id="q3-fam" rows={momentum}>
          {(pick) => (
            <RankedBars
              rows={pick.map((r) => ({
                label: r.f,
                value: r.gap,
                color: r.gap >= 0 ? '--good' : '--bad',
                mode: 'pct',
                onClick: () => famDrill(r.f),
                big: [[fmt(r.jobs), 'Jobs today']],
                extra: [
                  ['Change since 2021', (r.chgPct >= 0 ? '+' : '') + r.chgPct.toFixed(1) + '%'],
                  ['Projected by 2030', (r.g5pct >= 0 ? '+' : '') + r.g5pct.toFixed(1) + '%'],
                  ['Annual openings', fmt(r.open)],
                ],
              }))}
              opts={{
                mode: 'pct',
                signed: true,
                valueLabel: 'Projection minus what happened',
                clickHint: 'Click for the occupations inside it',
                aria: 'Projected growth against observed change by occupation group',
              }}
            />
          )}
        </Ranked>
      ),
    },
  };

  // ---- what postings ask for ---------------------------------------------"""),

    # the rows the fourth measure ranks
    ("""  const growers = fams
    .filter((r) => r.g5pct !== null)
    .sort((a, b) => b.g5pct - a.g5pct);""",
     """  const growers = fams
    .filter((r) => r.g5pct !== null)
    .sort((a, b) => b.g5pct - a.g5pct);

  // Both halves have to exist for the difference to mean anything, so a group
  // missing either is left out rather than counted as zero.
  const momentum = fams
    .filter((r) => r.g5pct !== null && r.chgPct !== null)
    .map((r) => ({ ...r, gap: r.g5pct - r.chgPct }))
    .sort((a, b) => b.gap - a.gap);"""),

    # ------------------------------------------- general demand: no ratio --
    ("""      // Postings per job is the guard against reading column height as demand.
      // It is the number that explains Washington County.
      note: a.perJob ? a.perJob.toFixed(2) + '/job' : null,""",
     """      // No postings-per-job figure under the column. Each column sums to 100%
      // and encodes no height at all, so it was guarding against a misreading
      // the chart shape already prevents -- and a second number under every
      // column competes with the four-way split that is the chart. It is still
      // in the table underneath, which demandCols carries.
      note: null,"""),

    ("""                  market. The figure under each Vermont column is postings per job, which
                  is what keeps a county that advertises heavily from reading as a county
                  that hires heavily.""",
     """                  market. Postings per job, which separates a place that advertises
                  heavily from one that hires heavily, is in the table under the chart."""),

    ("""        `what employers write down, not what every job requires. The figure under each column ` +
        `is postings per job, which is how to tell a place that advertises heavily from one ` +
        `that hires heavily.` +""",
     """        `what employers write down, not what every job requires.` +"""),

    # ------------------------------------------ the section gets the picker --
    ("""                  is advertised, and what is projected by 2030. They disagree, which is the
                  reason to look at more than one.
                </HowTo>
                <Picker id="q3-measure" label="Measure" options={DEMAND_MEASURES}>""",
     """                  is advertised, what is projected by 2030, and whether that projection is
                  faster or slower than what already happened. They disagree, which is the
                  reason to look at more than one. Click any bar for the occupations inside
                  it, priced against the benchmark below.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                <Picker id="q3-measure" label="Measure" options={DEMAND_MEASURES}>"""),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("%d occurrences of %r" % (s.count(old), old[:80]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Q3.js patched,", len(s), "bytes")
