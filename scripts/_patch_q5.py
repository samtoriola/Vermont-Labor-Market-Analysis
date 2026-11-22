"""Rebuilds both Opportunities sections. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))


def edit(rel, pairs):
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, "%s: %d occurrences of %r" % (rel, s.count(old), old[:80])
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(rel, "patched,", len(s), "bytes")


# ---- the read-out now carries the finding the chart is shaded by ------------
edit("lib/insight.js", [(
    """  const pc = (all.length / universe) * 100;
  return found(
    `${fmt(all.length)} of ${fmt(universe)} occupations clear the screen (${pc.toFixed(1)}%), ` +
    `and ${fmt(acted.length)} of those show movement on at least two signals without an ` +
    `established VSCS pipeline.`
  );""",
    """  const pc = (all.length / universe) * 100;
  // The pipeline split is the answer to the section's own question, and it used to
  // be a column a reader had to sort by to find.
  const bare = all.filter((r) => !r.linked);
  const bareOpen = bare.reduce((a, r) => a + (r.o || 0), 0);
  const hardest = bare.slice().sort((a, b) => b.o - a.o)[0];
  return found(
    `${fmt(all.length)} of ${fmt(universe)} occupations clear the screen (${pc.toFixed(1)}%), ` +
    `and ${fmt(acted.length)} of those show movement on at least two signals without an ` +
    `established VSCS pipeline. ` +
    (bare.length
      ? `${fmt(bare.length)} have no VSCS pipeline at all, carrying ${fmt(bareOpen)} openings ` +
        `a year between them${hardest ? `, most of any in ${shortLabel(hardest.n)}` : ''}.`
      : 'Every one of them has some VSCS pipeline behind it.')
  );"""
)])

# ---- Q5 --------------------------------------------------------------------
edit("components/views/Q5.js", [
    # imports
    ("""import { Callout, HowTo, Panel, Picker, Ranked, VHead, N } from '../ui';""",
     """import { Callout, HowTo, Legend, Panel, Picker, Ranked, VHead, N } from '../ui';"""),
    ("""import { RankedBars } from '../charts';""",
     """import { RankedBars, StackedRows } from '../charts';"""),
    ("""import DataTable from '../DataTable';
import { useDrill, occDrill } from '../Drill';""",
     """import DataTable from '../DataTable';
import { Split } from '../Detail';
import { useDrill, occDrill } from '../Drill';"""),

    # the four components, and what the pane shows for a scored occupation
    ("""  const O = SOW.opp;""",
     """  const O = SOW.opp;

  /**
   * THE SCORE, UNPACKED
   * -------------------
   * The score is the mean of four percentile ranks at 25% each, and the chart used
   * to draw only the mean. Two occupations two points apart can be nothing alike:
   * Registered Nurses score 79.7 off the 99th percentile for size and the 52nd for
   * growth, Computer Network Architects 77.5 off the 23rd and the 96th. One is a
   * large occupation that is not growing; the other is a small one growing fast,
   * and they call for different responses. The four ranks were on the hover, which
   * put the chart's argument in a tooltip.
   *
   * So the bar is split into what it is made of. Length is unchanged, so the
   * ranking is unchanged and nothing a reader learned is now wrong -- they can
   * just see which legs a score stands on.
   *
   * The ramp skips --ord3: four segments from one hue need the contrast between
   * neighbours more than they need even spacing.
   */
  const COMPS = [
    { k: 's_size', label: 'Employment', color: '--ord5' },
    { k: 's_growth', label: 'Growth', color: '--ord4' },
    { k: 's_postings', label: 'Advertising', color: '--ord2' },
    { k: 's_pay', label: 'Pay', color: '--ord1' },
  ];

  const occDrillFor = (r, from) =>
    open(
      occDrill({
        label: 'Occupation group',
        title: r.f,
        cap: `Opened from ${r.n}. Every occupation in this group.`,
        occ: occByFamily(r.f),
        lwAnnual: LWA,
      })
    );

  const scoreDetail = (r) => ({
    label: 'Occupation',
    title: r.n,
    stats: [
      [r.sc.toFixed(1), 'Opportunity score'],
      [fmt(r.j), 'Jobs today'],
      [r.m ? money(r.m) : '\\u2014', 'Typical pay'],
    ],
    note: `Each rank is this occupation against the ${fmt(O.nEligible)} scored ones, on that measure alone.`,
    cols: ['Component', 'Rank', 'Behind it'],
    rows: [
      ['Employment', r.s_size, fmt(r.j) + ' jobs'],
      [
        'Growth',
        r.s_growth,
        r.g === null || r.g === undefined ? '\\u2014' : (r.g > 0 ? '+' : '') + r.g + '% by 2030',
      ],
      ['Advertising', r.s_postings, r.pp + ' ads per 100'],
      ['Pay', r.s_pay, r.m ? money(r.m) : '\\u2014'],
    ],
    more: { label: `All occupations in ${r.f}`, onClick: () => occDrillFor(r) },
  });

  // What the pane shows for a screened candidate: the three figures the bar
  // carries, then the three signal tests spelled out rather than counted.
  const PIPE_COLOR = {
    [SUPPLY.none]: '--ord5',
    [SUPPLY.thin]: '--ord3',
    [SUPPLY.established]: '--ord1',
  };
  const candDetail = (r) => ({
    label: 'Candidate',
    title: r.n,
    stats: [
      [fmt(r.o), 'Openings a year'],
      [r.linked ? r.linked.toFixed(1) : 'none', 'Graduates attributed'],
      [r.m ? money(r.m) : '\\u2014', 'Typical pay'],
    ],
    note: `${r.supply}. Each signal is judged against other occupations needing ${r.t.toLowerCase()}.`,
    cols: ['Signal', 'This', 'Passes'],
    rows: [
      ['Openings per 100 jobs', r.opRate.toFixed(1), r.signals.includes('openings') ? 'yes' : 'no'],
      ['Ads per 100 jobs', r.postRate.toFixed(1), r.signals.includes('postings') ? 'yes' : 'no'],
      [
        'Projected by 2030',
        r.g === null || r.g === undefined ? '\\u2014' : (r.g > 0 ? '+' : '') + r.g + '%',
        r.signals.includes('growth') ? 'yes' : 'no',
      ],
    ],
    more: { label: `All occupations in ${r.f}`, onClick: () => occDrillFor(r) },
  });"""),

    # the chart for Highest scoring
    ("""                        <Ranked id="q5-score" rows={shown} show={20}>
                          {(pick) => (
                            <RankedBars
                              rows={pick.map((r) => ({
                                label: r.n,
                                value: r.sc,
                                color: '--s1',
                                dec: 1,
                                extra: [
                                  ['Jobs', fmt(r.j)],
                                  ['Median earnings', money(r.m)],
                                  ['25th percentile', money(r.p25)],
                                  ['Median vs living wage', r.lw + '×'],
                                  ['p25 vs living wage', r.lw25 + '×'],
                                  ['Annual openings (context only)', fmt(r.o) + ' (' + r.op + ' per 100 jobs)'],
                                  ['Postings per 100 jobs', r.pp],
                                  ['5-yr growth', r.g + '%'],
                                  ['Entry credential', r.t],
                                  [`— scored components, ${O.weightEach}% each —`, ''],
                                  ['Employment', r.s_size],
                                  ['Growth', r.s_growth],
                                  ['Postings intensity', r.s_postings],
                                  ['Median pay', r.s_pay],
                                ],
                              }))}
                              opts={{
                                dec: 1,
                                labelWidth: 262,
                                max: 100,
                                valueLabel: 'Opportunity score',
                                aria: 'Highest-scoring occupations',
                              }}
                            />
                          )}
                        </Ranked>""",
     """                        <Legend
                          labels={COMPS.map((c) => c.label)}
                          colors={COMPS.map((c) => c.color)}
                        />
                        <Split items={shown} keyOf={(r) => r.n} detail={scoreDetail}>
                          {(select, active, width) => (
                            <Ranked id="q5-score" rows={shown} show={20}>
                              {(pick) => (
                                <StackedRows
                                  rows={pick.map((r) => ({
                                    label: r.n,
                                    // Fixed total with the parts in the same units as
                                    // the axis: the bar ends at the score, and each
                                    // segment is one rank's quarter of it.
                                    total: 100,
                                    parts: COMPS.map((c) => ({
                                      v: r[c.k] / 4,
                                      extra: [
                                        ['Jobs', fmt(r.j)],
                                        ['Typical pay', r.m ? money(r.m) : '—'],
                                        ['Openings a year', fmt(r.o)],
                                        ['Ads per 100 jobs', r.pp],
                                        ['Projected by 2030', r.g === null || r.g === undefined ? '—' : r.g + '%'],
                                        ['Entry credential', r.t],
                                      ],
                                    })),
                                    hi: r.sc.toFixed(1),
                                    onClick: () => select(r.n),
                                    active: active === r.n,
                                  }))}
                                  opts={{
                                    width,
                                    labelWidth: 262,
                                    ticks: [0, 25, 50, 75, 100],
                                    axisMax: 100,
                                    absolute: true,
                                    partFmt: (v) => String(Math.round(v * 4)),
                                    shareLabel: 'Percentile rank',
                                    tierNames: COMPS.map((c) => c.label),
                                    colors: COMPS.map((c) => c.color),
                                    rightLabel: 'SCORE',
                                    clickHint: 'Click for its four ranks and its group',
                                    aria:
                                      'Highest-scoring occupations, each bar split into the four ranks it is the mean of',
                                  }}
                                />
                              )}
                            </Ranked>
                          )}
                        </Split>"""),

    # the Highest scoring copy
    ("""                          `Each occupation is ranked against all the others on four things — how many it employs, how fast it is growing, how heavily it is advertised, and what it pays — and the four ranks are averaged. Hover a bar for its four scores.` +""",
     """                          `Each occupation is ranked against all the others on four things — how many it employs, how fast it is growing, how heavily it is advertised, and what it pays — and the four ranks are averaged. The bar is that average; the segments are the four ranks it is made of, each contributing up to a quarter of the length. An even bar is strong on everything; a lopsided one is a bet on one thing. Click a bar for its ranks and the occupations around it.` +"""),
    ("""                  One score per occupation, the average of four percentile ranks: how many
                  it employs, how fast it is growing, how heavily it is advertised, and
                  what it pays. Pick a credential to see the highest scorers that ask for
                  it. The score is the same either way — a credential narrows the list, it
                  does not re-grade it.""",
     """                  One score per occupation, the average of four percentile ranks: how many
                  it employs, how fast it is growing, how heavily it is advertised, and
                  what it pays. Each bar is split into those four, so a score you can see
                  the inside of. Pick a credential to see the highest scorers that ask for
                  it — the score is the same either way, a credential narrows the list, it
                  does not re-grade it."""),

    # Program candidates: a chart above the table it already had
    ("""                {controls}
                <DataTable
                  cols={screenCols()}
                  rows={screened}
                  initialSort={{ k: 'o', dir: -1 }}
                  exportLabel="program-opportunities"
                  rowKey={(r) => r.s}
                  onRowClick={screenDrill}
                  pageSize={30}
                />""",
     """                {controls}
                <Legend
                  labels={[SUPPLY.none, SUPPLY.thin, SUPPLY.established]}
                  colors={[PIPE_COLOR[SUPPLY.none], PIPE_COLOR[SUPPLY.thin], PIPE_COLOR[SUPPLY.established]]}
                />
                <Split items={screened} keyOf={(r) => r.s} detail={candDetail}>
                  {(select, active, width) => (
                    <Ranked id="q5-screen" rows={screened} show={16}>
                      {(pick) => (
                        <RankedBars
                          rows={pick.map((r) => ({
                            label: r.n,
                            value: r.o,
                            // Shaded by pipeline rather than ranked by it, so the
                            // order stays the one a reader expects -- hardest hiring
                            // first -- and the gap shows without a sort.
                            color: PIPE_COLOR[r.supply] || '--ord3',
                            right: r.linked ? r.linked.toFixed(1) : 'none',
                            right2: r.nSignals + ' of 3',
                            onClick: () => select(r.s),
                            active: active === r.s,
                            big: [[r.supply, 'VSCS pipeline']],
                            extra: [
                              ['Jobs', fmt(r.j)],
                              ['Typical pay', r.m ? money(r.m) : '—'],
                              ['Projected by 2030', r.g === null || r.g === undefined ? '—' : r.g + '%'],
                              ['Signals', r.signals.length ? r.signals.join(', ') : 'none'],
                              ['Entry credential', r.t],
                            ],
                          }))}
                          opts={{
                            width,
                            labelWidth: 290,
                            valueLabel: 'Openings a year',
                            valueHead: 'OPENINGS',
                            rightHead: 'GRADUATES',
                            rightHead2: 'SIGNALS',
                            clickHint: 'Click for its signals and its group',
                            aria:
                              'Occupations clearing the screen, by annual openings, shaded by VSCS pipeline',
                          }}
                        />
                      )}
                    </Ranked>
                  )}
                </Split>
                <DataTable
                  cols={screenCols()}
                  rows={screened}
                  initialSort={{ k: 'o', dir: -1 }}
                  exportLabel="program-opportunities"
                  rowKey={(r) => r.s}
                  onRowClick={screenDrill}
                  pageSize={30}
                />"""),

    # Program candidates copy
    ("""                cap={`Occupations that pass four tests at once: at least ${minOpen} openings a year, pay at or above the living wage, and a credential VSCS already awards${excludeObvious ? ', and not one of the 25 largest' : ''}. Signals counts how many of three things an occupation has going for it — openings, advertising and projected growth — each judged against others needing the same credential. Click a row for its occupation group.`}""",
     """                cap={`Occupations that pass four tests at once: at least ${minOpen} openings a year, pay at or above the living wage, and a credential VSCS already awards${excludeObvious ? ', and not one of the 25 largest' : ''}. The bar is annual openings and its shade is how much VSCS already produces for that work, so the order stays the one that matters while the gap shows without a sort. Signals counts how many of three things an occupation has going for it — openings, advertising and projected growth — each judged against others needing the same credential. Click a bar or a row for the detail.`}"""),
    ("""                  A screen, not a ranking: set the four tests below and the table shows
                  what passes all of them. It is a list of places to look, never a
                  recommendation — the scope of this work stops short of saying whether a
                  program should be created, expanded or cut.""",
     """                  A screen, not a ranking: set the four tests below and the chart shows
                  what passes all of them, shaded by how much VSCS already produces for
                  it. It is a list of places to look, never a recommendation — the scope
                  of this work stops short of saying whether a program should be created,
                  expanded or cut."""),
])
