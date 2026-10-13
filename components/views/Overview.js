'use client';

import {
  DATA, LC, TOTJ, GLANCE, tierRow, cpsSubBacc, cpsHsOrLess, lwHourly,
} from '@/lib/data';
import { fmt } from '@/lib/format';
import { Panel, Legend, Tiles } from '../ui';
import { RankedBars } from '../charts';
import { requirementsGap } from '@/lib/insight';

export default function Overview({ lw }) {
  const lastCps = DATA.trend[DATA.trend.length - 1];
  const baReq = tierRow("Bachelor's").share + tierRow('Graduate / professional').share;
  const sub = tierRow('Sub-baccalaureate');

  const tiles = [
    ['Jobs, 2025', fmt(LC.totalJobs), 'All 798 occupations'],
    ['Employed Vermonters', fmt(lastCps.emp), '2025, 11-month average'],
    ['Living wage', '$' + lwHourly(lw).toFixed(2), lw],
    ['Require BA+', baReq.toFixed(1) + '%', 'of jobs, by entry education'],
    ['Hold a degree', lastCps.ba.toFixed(1) + '%', 'of workers 25 and over'],
    ['Annual openings', fmt(LC.openTotal / LC.openYears), LC.window],
  ];

  // The chart draws six bars; read as three comparisons, which is what the table
  // under it lays out, gap included.
  const gaps = () => {
    const hsJobs = tierRow('High school').share + tierRow('No formal credential').share;
    return [
      { level: 'Bachelor’s or more', jobs: baReq, people: lastCps.ba },
      { level: 'Sub-baccalaureate', jobs: sub.share, people: cpsSubBacc() },
      { level: 'High school or less', jobs: hsJobs, people: cpsHsOrLess() },
    ].map((r) => ({ ...r, gap: r.people - r.jobs }));
  };

  const contrast = [
    { label: 'Jobs requiring BA+', value: baReq, color: '--s1' },
    { label: 'Workers holding BA+', value: lastCps.ba, color: '--s3' },
    { label: 'Jobs requiring sub-bacc.', value: sub.share, color: '--s1' },
    { label: 'Workers holding sub-bacc.', value: cpsSubBacc(), color: '--s3' },
    {
      label: 'Jobs requiring HS or less',
      value: tierRow('High school').share + tierRow('No formal credential').share,
      color: '--s1',
    },
    { label: 'Workers holding HS or less', value: cpsHsOrLess(), color: '--s3' },
  ];

  // CPS only, one vintage, so nothing on this panel mixes surveys. Total employment
  // is already in the tile row above, so this covers the structure around it.
  const G = GLANCE;
  const glanceTiles = [
    ['Full-time', G.ftShare.toFixed(1) + '%', fmt(G.ft) + ' working 35+ hours'],
    ['Part-time', G.ptShare.toFixed(1) + '%', fmt(G.pt) + ' working under 35'],
    [
      'Labor force participation',
      G.lfpr.toFixed(1) + '%',
      fmt(G.lf) + ' of ' + fmt(G.pop16) + ' aged 16+',
    ],
    [
      'Unemployment',
      G.ur.toFixed(2) + '%',
      '±' + G.urCi.toFixed(2) + ' points, 95% interval',
    ],
  ];

  return (
    <>
      <Tiles items={tiles} />

      <Panel
        title="Do Vermont’s jobs ask for the credentials its workers hold?"
        note={requirementsGap(baReq, lastCps.ba)}
        cap="One side counts what jobs ask for, the other what workers hold. They come from different surveys counting different populations, so compare the shares rather than the levels."
        src="Vermont occupation data, 2025 · labor force survey, 2025, age 25 and over"
        data={{
          cols: [
            { k: 'level', label: 'Credential', kind: 'text', get: (r) => r.level },
            { k: 'jobs', label: 'Share of jobs asking for it', kind: 'rate', get: (r) => r.jobs },
            { k: 'people', label: 'Share of workers holding it', kind: 'rate', get: (r) => r.people },
            { k: 'gap', label: 'Gap, workers minus jobs', kind: 'pct', get: (r) => r.gap },
          ],
          rows: gaps(),
          label: 'credentials-jobs-vs-workers',
          unit: 'credentials',
        }}
      >
        <Legend
          labels={['What jobs ask for', 'What workers hold']}
          colors={['--s1', '--s3']}
        />
        <RankedBars
          rows={contrast}
          opts={{
            mode: 'pct',
            labelWidth: 214,
            valueLabel: 'Share',
            aria: 'Requirements versus attainment',
          }}
        />
      </Panel>

      <Panel
        title="How many Vermonters are working, and on what terms?"
        src={`Labor force survey, Vermont ${G.year} · ${G.months}-month average`}
      >
        <Tiles items={glanceTiles} />
      </Panel>

    </>
  );
}
