'use client';

import { LC, PCT, TOTJ, lwAnnual, occByFamily } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Panel, Legend, Tiles, LwPicker } from '../ui';
import { RankedBars } from '../charts';
import { useDrill, occDrill } from '../Drill';
import { Split, occDetail } from '../Detail';
import { pricedPool, rollUp, rollUpBy } from '@/lib/wage';
import { marketShape } from '@/lib/insight';

/**
 * One chart that is the Vermont labour market.
 *
 * The Overview used to carry ten figures across two tile rows and one chart,
 * which is a lot of reading and no argument. It is the only page that has to
 * work for someone who will not click anything else, and a grid of headline
 * numbers does not tell that reader what the analysis found.
 *
 * So: every occupation group on one chart, as long as it is big and as dark as
 * its work is underpaid. Two measures in one mark -- length for scale, fill for
 * how much of it pays below a living wage -- which is the only way the state
 * fits on one screen without the reader doing the joining themselves. Office &
 * Admin Support and Food Preparation are nearly the same size and at opposite
 * ends of the shading, and that contrast is the finding.
 *
 * THE RAMP
 * --ord1 to --ord5, the house sequential scale the concentration grid and the
 * age mix already use. Not a red one: red reads as a warning that the reader is
 * meant to act on, and this is a measurement. The ramp inverts between light and
 * dark so that ord1 is always the least and ord5 the most.
 *
 * WHAT LEFT
 * The jobs-require-against-workers-hold chart and the four labour-force tiles.
 * The first is the only panel that deliberately crosses units and is worth
 * putting back somewhere; it is a one-line restore.
 */

// Bands for the fill. Cut where the answers differ rather than at even
// intervals: under a tenth and over three quarters are different kinds of work,
// and the middle three are where most of the groups actually land.
const BANDS = [
  { max: 10, color: '--ord1', label: 'Under 10%' },
  { max: 30, color: '--ord2', label: '10 to 30%' },
  { max: 50, color: '--ord3', label: '30 to 50%' },
  { max: 75, color: '--ord4', label: '50 to 75%' },
  { max: Infinity, color: '--ord5', label: '75% and over' },
];

function bandOf(pc) {
  return (BANDS.filter((b) => pc < b.max)[0] || BANDS[BANDS.length - 1]).color;
}

export default function Overview({ lw, setLw }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();

  // Only occupations carrying a usable pay ladder can be shaded at all, so the
  // bars are drawn over the priced pool and the source line says how much of the
  // state that is.
  const pool = pricedPool(LC.allOcc);
  const head = rollUp(pool, LWA);
  const groups = rollUpBy(pool, (o) => o.f, LWA).sort((a, b) => b.jobs - a.jobs);

  const tiles = [
    ['Jobs', fmt(TOTJ), `across ${fmt(LC.allOcc.length)} occupations`],
    ['The typical job pays', money(PCT.statewide.p50), `living wage ${money(LWA)}`],
    [
      'Pay below it',
      head ? head.below.toFixed(0) + '%' : '—',
      head ? `${fmt(head.belowN)} jobs` : '',
    ],
  ];

  const groupDrill = (r) =>
    open(
      occDrill({
        label: 'Occupation group',
        title: r.f,
        cap: 'Every occupation in this group, largest first.',
        occ: occByFamily(r.f),
        lwAnnual: LWA,
      })
    );

  // What the pane beside the chart shows: the three figures the bar encodes,
  // then the largest occupations inside the group, then the way through to the
  // whole table. The same shape Employment opens, because it is the same click.
  //
  // The list is every occupation in the group, not only the priced ones the bar
  // was drawn over -- the pane answers "what work is this", and an occupation
  // without a published pay ladder is still part of the answer.
  const groupDetail = (r) =>
    occDetail({
      label: 'Occupation group',
      title: r.f,
      occ: occByFamily(r.f),
      lwAnnual: LWA,
      stats: [
        [fmt(r.jobs), 'Jobs today'],
        [r.below.toFixed(0) + '%', 'Below a living wage'],
        [fmt(r.belowN), 'Jobs short'],
      ],
      onMore: () => groupDrill(r),
    });

  const bar = (r, select, active) => ({
    label: r.f,
    value: r.jobs,
    color: bandOf(r.below),
    right: r.below.toFixed(0) + '%',
    onClick: () => select(r.f),
    active: active === r.f,
    big: [[r.below.toFixed(1) + '%', 'Below the benchmark']],
    extra: [
      ['Jobs below it', fmt(r.belowN)],
      ['At or above it', fmt(r.jobs - r.belowN)],
      ['Share of all Vermont jobs', ((r.jobs / TOTJ) * 100).toFixed(1) + '%'],
      ['Occupations', fmt(r.nocc)],
      ...(r.worst
        ? [['Most jobs short', `${r.worst.o.n} (${fmt(Math.round(r.worst.n))})`]]
        : []),
    ],
  });

  return (
    <>
      <Tiles items={tiles} />

      <LwPicker value={lw} onChange={setLw} />

      <Panel
        title="What Vermont does for a living, and how much of it pays enough"
        note={marketShape(groups, head ? head.jobs : TOTJ)}
        cap={`Bar length is jobs. Shading is the share of that group’s jobs paying below a living wage for ${lw}, read off each occupation’s own pay distribution rather than from its median. Click any bar for the occupations inside it.`}
        src={`Vermont occupation data, 2025 · ${fmt(head ? head.jobs : 0)} jobs with a published pay distribution · benchmark ${money(LWA)} a year (${lw})`}
        data={{
          cols: [
            { k: 'f', label: 'Occupation group', kind: 'text', get: (r) => r.f },
            { k: 'jobs', label: 'Jobs', kind: 'num', get: (r) => r.jobs },
            {
              k: 'share',
              label: 'Share of all jobs',
              kind: 'rate',
              get: (r) => (r.jobs / TOTJ) * 100,
            },
            { k: 'below', label: 'Share below the benchmark', kind: 'rate', get: (r) => r.below },
            { k: 'belowN', label: 'Jobs below it', kind: 'num', get: (r) => r.belowN },
            { k: 'nocc', label: 'Occupations', kind: 'num', get: (r) => r.nocc },
          ],
          rows: groups,
          label: 'vermont-at-a-glance',
          initialSort: { k: 'jobs', dir: -1 },
          unit: 'occupation groups',
        }}
      >
        <Legend
          labels={BANDS.map((b) => b.label)}
          colors={BANDS.map((b) => b.color)}
        />
        <Split items={groups} keyOf={(r) => r.f} detail={groupDetail}>
          {(select, active, width) => (
            <RankedBars
              rows={groups.map((r) => bar(r, select, active))}
              opts={{
                width,
                // The fill is the second measure here, so a chosen bar must not
                // fade the other twenty-one into one colour.
                keepFill: true,
                labelWidth: 206,
                valueLabel: 'Jobs',
                valueHead: 'JOBS',
                rightHead: 'BELOW',
                clickHint: 'Click for the occupations inside it',
                aria:
                  'Vermont employment by occupation group, shaded by how much of it pays below a living wage',
              }}
            />
          )}
        </Split>
      </Panel>
    </>
  );
}
