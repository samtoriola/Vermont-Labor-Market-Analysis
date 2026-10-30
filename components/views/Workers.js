'use client';

// Section: Workers
import { PEOPLE, lwAnnual } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { peopleCols } from '@/lib/tables';
import { HowTo, Panel, VHead, LwPicker } from '../ui';
import { RankedBars } from '../charts';
import Sections from '../Sections';
import { meanMedianGap, peopleLadderStep } from '@/lib/insight';

/**
 * The two panels that count people rather than jobs.
 *
 * They were one section under Wage quality and one under Pathways, each sitting
 * beside panels built from occupation data. The About tab already states the
 * rule -- the occupation data counts jobs, the household survey counts people,
 * and the two are not interchangeable -- but the navigation did not follow it,
 * so a reader moving between neighbouring sections changed unit with nothing
 * saying so. Here the unit is the group, and every caption says it again.
 */
export default function Workers({ lw, setLw, section }) {
  const LWA = lwAnnual(lw);

  // One bar per place at the midpoint earner, Vermont in colour and the
  // neighbouring state and the country in grey behind it. The bar is the
  // midpoint, so the average -- which sits well above it -- is on the hover
  // with the range.
  const areaBars = PEOPLE.byArea.map((a, i) => ({
    label: a.label,
    value: a.med,
    color: i > 0 ? '--ink-3' : a.med >= LWA ? '--s3' : '--s2',
    extra: [
      ['Times the living wage', (a.med / LWA).toFixed(2) + '×'],
      ['Average earnings', money(a.avg)],
      ['Middle half earns', money(a.p25) + ' to ' + money(a.p75)],
      ['Lowest-paid tenth', money(a.p10)],
      ['Highest-paid tenth', money(a.p90)],
      ['Respondents', fmt(a.n)],
      ['Workers represented', fmt(a.pop)],
    ],
  }));

  const credBars = PEOPLE.byCred.map((c) => ({
    label: c.thin ? c.label + ' (small sample)' : c.label,
    value: c.med,
    color: c.thin ? '--ink-3' : c.med >= LWA ? '--s3' : '--s2',
    extra: [
      ['Times the living wage', (c.med / LWA).toFixed(2) + '×'],
      ['Average earnings', money(c.avg)],
      ['Middle half earns', money(c.p25) + ' to ' + money(c.p75)],
      ['Lowest-paid tenth', money(c.p10)],
      ['Highest-paid tenth', money(c.p90)],
      ['Respondents', fmt(c.n)],
    ],
  }));

  return (
    <>
      <VHead title="Workers">
        What do Vermonters themselves earn, and what does the credential a worker holds —
        rather than the one a job asks for — lead to?
      </VHead>

      <Sections
        id="workers"
        active={section}
        items={[
          {
            id: 'what-people-hold',
            label: 'What people hold',
            render: () => (
              <>
                <HowTo>
                  Every figure here counts <strong>people</strong>, from a household survey —
                  not jobs. Pathways asks the same question of the job; the two do not match,
                  and are not meant to.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="What does each rung pay, by the credential workers hold?"
                  note={peopleLadderStep(PEOPLE.byCred)}
                  cap="The credential ladder measured on people rather than jobs: what the midpoint Vermonter earns at each credential they hold. The self-employed and the military are left out. A bar marked as a small sample rests on fewer than 100 answers and is rough. Hover for the average and the range."
                  src={`Census household survey, 2024 · ${PEOPLE.universe.toLowerCase()} · living-wage benchmark 2025, ${lw}`}
                  data={{ cols: peopleCols('Credential held'), rows: PEOPLE.byCred, label: 'pay-by-credential-held',
                          initialSort: { k: 'med', dir: -1 }, unit: 'credentials',
                          note: 'Groups, not the individual dots: each dot is one anonymous respondent.' }}
                >
                  <RankedBars
                    rows={credBars}
                    opts={{
                      money: true,
                      rule: LWA,
                      ruleLabel: 'Living wage',
                      valueLabel: 'Midpoint earnings',
                      labelWidth: 236,
                      aria: 'Midpoint earnings by credential held',
                    }}
                  />
                </Panel>
              </>
            ),
          },
          {
            id: 'what-people-earn',
            label: 'What people earn',
            render: () => (
              <>
                <HowTo>
                  The midpoint <strong>worker</strong>, not the midpoint job. Vermont is in
                  colour; the grey bars are the two benchmarks the pay charts use throughout.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                <Panel
                  title="What do individual Vermonters actually earn?"
                  note={meanMedianGap(PEOPLE.byArea[0])}
                  cap="What the midpoint Vermonter on a wage or salary earned that year, against the same figure for its nearest comparable state and the country. The self-employed and the military are left out, matching the occupation charts. Hover for the average and the range around it."
                  src={`Census household survey, 2024 · ${PEOPLE.universe.toLowerCase()} · living-wage benchmark 2025, ${lw}`}
                  data={{ cols: peopleCols('Place'), rows: PEOPLE.byArea, label: 'worker-earnings',
                          initialSort: { k: 'med', dir: -1 }, unit: 'places',
                          note: 'Groups, not the individual dots: each dot is one anonymous respondent.' }}
                >
                  <RankedBars
                    rows={areaBars}
                    opts={{
                      money: true,
                      rule: LWA,
                      ruleLabel: 'Living wage',
                      valueLabel: 'Midpoint earnings',
                      labelWidth: 236,
                      aria: 'Midpoint worker earnings by area',
                    }}
                  />
                </Panel>
              </>
            ),
          },
        ]}
      />
    </>
  );
}
