"""Rebuilds "Which credentials pay" as a year of openings, with the click-through
the other tabs carry. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "components", "views", "Q4.js")
s = io.open(P, encoding="utf-8").read()


def sub(old, new, n=1):
    global s
    assert s.count(old) == n, "%d occurrences of %r" % (s.count(old), old[:80])
    s = s.replace(old, new)


# ---- imports ---------------------------------------------------------------
sub("import { pooledLadder, rollUp } from '@/lib/wage';",
    "import { pooledLadder, rollUp, rollUpOn, shareBelow, occBox } from '@/lib/wage';")
sub("import { bandCols, credLadderCols } from '@/lib/tables';",
    "import { bandCols, credLadderCols, openingsCols } from '@/lib/tables';")
sub("import { Callout, HowTo, Panel, Picker, Table, VHead, LwPicker, N } from '../ui';",
    "import { Callout, HowTo, Legend, Panel, Picker, VHead, LwPicker, N } from '../ui';")
sub("import { funnelContrast, ladderShape, largestCategory } from '@/lib/insight';",
    "import { openingsSplit, ladderShape, largestCategory } from '@/lib/insight';")
sub("import { RankedBars, RangeRows } from '../charts';",
    "import { occOpenCols } from '../occCols';\nimport { RankedBars, RangeRows } from '../charts';")

# ---- the rows the openings chart is drawn from ------------------------------
sub("""  const lo = Math.min(...ladder.map((r) => r.box.p10));""",
    """  /**
   * A year of hiring at each credential, split by the benchmark.
   *
   * The section used to count DOORS: occupations clearing a volume screen and
   * then a pay screen, 3 of 106 at the bottom of the ladder. Two things were
   * wrong with it as the headline. The screen changed meaning up the ladder --
   * at the bottom the pay test is what bites, at the top only 9 of 76 graduate
   * occupations clear the volume test at all and every one of them pays -- so
   * one number per row could not say which test a rung was failing. And the
   * openings column it printed was gated the same way, which is defensible for
   * counting doors and not for counting openings: it threw away a whole
   * occupation over a few hundred dollars on its median, and every employer too
   * small to hire 50 a year with it.
   *
   * So this counts the openings themselves, weighted by each occupation's own
   * pay distribution and with no volume screen. The figures move a long way --
   * no formal credential goes 9% to 16%, a bachelor's 73% to 91% -- and the
   * ordering is the same, which is what you would expect if the old number was
   * measuring the screen rather than the work.
   *
   * The doors count is not lost: it is a figure in the drill, where it answers
   * the question it is actually good for.
   */
  const openings = TIER_ORDER.map((key) => {
    const occ = occByTier(key);
    const roll = rollUpOn(occ, LWA, (o) => o.o || 0);
    const f = funnel.filter((x) => x.t === key)[0];
    if (!roll || !roll.total) return null;
    return {
      t: key,
      occ,
      openAll: roll.total,
      openPay: roll.total - roll.belowN,
      openShort: roll.belowN,
      share: 100 - roll.below,
      nocc: roll.nocc,
      nAll: f ? f.nAll : occ.length,
      nHiring: f ? f.nHiring : null,
      nPaying: f ? f.nPaying : null,
    };
  }).filter(Boolean);

  const openDrill = (r) =>
    open({
      label: 'Entry credential',
      title: r.t,
      cap:
        `Every occupation whose typical entry credential is this tier, most openings first. ` +
        `"Openings in work that pays" is each occupation's openings weighted by how much of ` +
        `it clears ${money(LWA)} a year, so an occupation that half clears it contributes half.`,
      occ: r.occ,
      cols: occOpenCols(LWA),
      initialSort: { k: 'o', dir: -1 },
      stats: [
        ['Occupations', fmt(r.nAll)],
        ['Openings a year', fmt(r.openAll)],
        ['In work that pays', fmt(r.openPay)],
        ['Share', r.share.toFixed(1) + '%'],
        // The old headline, kept where it is the right answer: this one is about
        // the occupation, not about its openings.
        [`Hiring ${MIN_OPEN}+ a year and paying`,
          r.nPaying === null ? '—' : `${r.nPaying} of ${r.nAll}`],
      ],
      src:
        'Search, filter and sort with the controls at the top; export downloads the filtered rows',
    });

  const openDetail = (r) => {
    const top = r.occ
      .filter((o) => o.o)
      .slice()
      .sort((a, b) => b.o - a.o)
      .slice(0, 8);
    return {
      label: 'Entry credential',
      title: r.t,
      stats: [
        [fmt(r.openAll), 'Openings a year'],
        [fmt(r.openPay), 'In work that pays'],
        [r.share.toFixed(0) + '%', 'Share of them'],
      ],
      note: `The ${top.length} occupations hiring most, of ${fmt(r.nAll)}.`,
      cols: ['Occupation', 'Openings', 'Pays it'],
      rows: top.map((o) => {
        const b = shareBelow(occBox(o), LWA);
        return [shortLabel(o.n), fmt(o.o), b === null ? '—' : (100 - b).toFixed(0) + '%'];
      }),
      more: {
        label: `All ${fmt(r.nAll)} occupations, with every measure`,
        onClick: () => openDrill(r),
      },
    };
  };

  const lo = Math.min(...ladder.map((r) => r.box.p10));""")

# ---- the section ------------------------------------------------------------
old_sec = s[s.index("            id: 'which-credentials-pay',"):s.index("          // --- Hidden for now ---")]
new_sec = """            id: 'which-credentials-pay',
            label: 'Which credentials pay',
            render: () => (
              <>
                <HowTo>
                  A year of hiring at each credential, and how much of it is in work
                  that pays a living wage. Openings, not jobs — this is what someone
                  leaving a credential actually meets. Click a bar for the occupations
                  hiring behind it.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="How much of a year&rsquo;s hiring at each credential pays a living wage?"
                  note={openingsSplit(openings)}
                  cap={`Every annual opening at each entry credential. The filled part is those in work paying at or above the benchmark, read off each occupation&rsquo;s own pay distribution and weighted by its openings — so an occupation whose midpoint clears the benchmark by a dollar contributes about half its openings, not all of them. No volume screen: an opening counts whether or not its occupation hires ${MIN_OPEN} a year. Each row is measured against its own openings, so the five do not add to 100%. Household: ${lw}.`}
                  src={`Vermont occupation data, 2025 · entry credential · annual openings · the benchmark&rsquo;s position read off each occupation&rsquo;s own 10th-to-90th percentile ladder, weighted by its openings · benchmark ${money(LWA)} a year (${lw})`}
                  data={{
                    cols: openingsCols(),
                    rows: openings,
                    label: 'openings-by-credential',
                    initialSort: { k: 'openAll', dir: -1 },
                    unit: 'credentials',
                    note:
                      'The last column is the old measure, kept because it answers a different question: how many occupations at this level both hire in volume and pay.',
                  }}
                >
                  <Legend
                    labels={['Openings in work that pays a living wage', 'The rest']}
                    colors={['--s1', '--track']}
                  />
                  <Split items={openings} keyOf={(r) => r.t} detail={openDetail}>
                    {(select, active, width) => (
                      <RankedBars
                        rows={openings.map((r) => ({
                          label: r.t,
                          value: r.openPay,
                          backdrop: r.openAll,
                          right: r.share.toFixed(0) + '%',
                          onClick: () => select(r.t),
                          active: active === r.t,
                          big: [[fmt(r.openAll), 'Openings a year']],
                          extra: [
                            ['In work that does not pay it', fmt(r.openShort)],
                            ['Occupations', fmt(r.nAll)],
                            [
                              `Hiring ${MIN_OPEN}+ a year and paying`,
                              r.nPaying === null ? '—' : `${r.nPaying} of ${r.nAll}`,
                            ],
                            ...(r.occ.filter((o) => o.o).length
                              ? [
                                  [
                                    'Hiring most',
                                    shortLabel(
                                      r.occ
                                        .filter((o) => o.o)
                                        .slice()
                                        .sort((a, b) => b.o - a.o)[0].n
                                    ),
                                  ],
                                ]
                              : []),
                          ],
                        }))}
                        opts={{
                          width,
                          labelWidth: 206,
                          valueLabel: 'Openings in work that pays',
                          valueHead: 'THAT PAY',
                          rightHead: 'SHARE',
                          clickHint: 'Click for the occupations hiring at this level',
                          aria:
                            'Annual openings by entry credential, with the share in work paying a living wage',
                        }}
                      />
                    )}
                  </Split>
                </Panel>
              </>
            ),
          },
"""
s = s.replace(old_sec, new_sec)

# shortLabel is used by the pane and the tooltip
sub("import Sections from '../Sections';",
    "import { shortLabel } from '@/lib/labels';\nimport Sections from '../Sections';")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Q4.js patched,", len(s), "bytes")
