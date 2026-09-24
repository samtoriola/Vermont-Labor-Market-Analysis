'use client';

import { DATA, LC, TOTJ, tierRow, cpsSubBacc, cpsHsOrLess, lwHourly } from '@/lib/data';
import { fmt } from '@/lib/format';
import { Panel, Legend, Table, Tiles, N } from '../ui';
import { RankedBars, TrendLine } from '../charts';

export default function Overview({ lw }) {
  const lastCps = DATA.trend[DATA.trend.length - 1];
  const baReq = tierRow("Bachelor's").share + tierRow('Graduate / professional').share;
  const sub = tierRow('Sub-baccalaureate');

  const tiles = [
    ['Jobs, 2025', fmt(LC.totalJobs), 'Lightcast, all 798 occupations'],
    ['CPS employment', fmt(lastCps.emp), '2025, 11-month average'],
    ['Living wage', '$' + lwHourly(lw).toFixed(2), lw],
    ['Require BA+', baReq.toFixed(1) + '%', 'of jobs, by entry education'],
    ['Hold BA+', lastCps.ba.toFixed(1) + '%', 'of workers 25+, CPS'],
    ['Annual openings', fmt(LC.openTotal / LC.openYears), 'Lightcast, ' + LC.window],
  ];

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

  return (
    <>
      <Tiles items={tiles} />

      <Panel
        title="Requirements versus attainment"
        cap="Two different questions, two different sources. Lightcast assigns each occupation a typical entry credential (a property of the job). CPS records the credential each worker holds (a property of the person). They are not the same measure."
        src="Lightcast occupation table, 2025 jobs · CPS 2025, age 25+ · CPS and Lightcast universes differ; compare shares, not levels"
      >
        <Legend
          labels={['Job requirement (Lightcast)', 'Worker attainment (CPS)']}
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

      <div className="grid2">
        <Panel
          title="CPS employment, 2021–2025"
          cap="Independent read on the employment base. 2025 is an 11-month average."
          src="CPS · SUM(WTFINL)/months"
        >
          <TrendLine
            series={{ x: DATA.trend.map((r) => r.y), y: DATA.trend.map((r) => r.emp) }}
            opts={{
              min: 300000,
              max: 360000,
              color: '--s3',
              aria: 'CPS employment',
              fmtY: (x) => Math.round(x / 1000) + 'k',
            }}
          />
        </Panel>

        <Panel
          title="Lightcast and CPS side by side"
          cap="Lightcast counts jobs; CPS counts employed residents. The ~3% difference is definitional, not an error."
          src="Neither is wrong; the universes differ"
        >
          <Table
            cols={['Measure', 'Value']}
            rows={[
              { cells: ['Lightcast jobs, 2025', fmt(LC.totalJobs)] },
              { cells: ['CPS employment, 2025', fmt(lastCps.emp)] },
              { cells: ['Difference', fmt(lastCps.emp - LC.totalJobs)] },
              { cells: ['Detailed occupations (Lightcast)', fmt(798)] },
              { cells: ['Occupational families (CPS)', fmt(DATA.families.length)] },
            ]}
          />
        </Panel>
      </div>
    </>
  );
}
