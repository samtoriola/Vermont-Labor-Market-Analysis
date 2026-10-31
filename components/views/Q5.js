'use client';

import { useState } from 'react';
import { LC, SOW, TIER_ORDER, lwAnnual, occByFamily } from '@/lib/data';
import { opportunityScreen, screenCols, SCREEN_TIERS, SUPPLY } from '@/lib/screen';
import { fmt, money } from '@/lib/format';
import { scoreCols } from '@/lib/tables';
import { Callout, HowTo, Panel, Picker, Ranked, VHead, N } from '../ui';
import Filters, { ActiveFilters } from '../Filters';
import { useFilters } from '../FilterContext';
import OccTable from '../OccTable';
import { RankedBars } from '../charts';
import Sections from '../Sections';
import { topScoreCredentials, screenYield, screenNarration } from '@/lib/insight';
import DataTable from '../DataTable';
import { useDrill, occDrill } from '../Drill';
import { LwPicker } from '../ui';

// Callout, N and screenNarration below are used only by the section(s) hidden further down. Kept
// imported so restoring one stays a single edit.

export default function Q5({ lw, setLw, section }) {
  const { apply } = useFilters();
  const { open } = useDrill();
  const LWA = lwAnnual(lw);

  // The screen's own criteria. Held here because two sections read them, and rendered
  // inside the panel they govern rather than above the whole tab.
  const [minOpen, setMinOpen] = useState(50);
  const [screenTiers, setScreenTiers] = useState(SCREEN_TIERS);
  const [excludeObvious, setExcludeObvious] = useState(true);
  const screened = opportunityScreen({
    lwAnnual: LWA, minOpen, tiers: screenTiers, excludeObvious,
  });
  const acted = screened.filter((r) => r.nSignals >= 2 && r.supply !== SUPPLY.established);
  const toggleTier = (t) =>
    setScreenTiers((cur) => (cur.includes(t) ? cur.filter((x) => x !== t) : cur.concat(t)));
  const screenDrill = (r) =>
    open(
      occDrill({
        label: 'Occupation group',
        title: r.f,
        cap: `Opened from ${r.n}. Every occupation in this group.`,
        occ: occByFamily(r.f),
        lwAnnual: LWA,
      })
    );
  const controls = (
    <div className="screenctl">
      <div className="scl">
        <span className="sclab">Minimum annual openings</span>
        <div className="chips">
          {[25, 50, 100].map((n) => (
            <button key={n} type="button" className={n === minOpen ? 'on' : undefined}
              aria-pressed={n === minOpen} onClick={() => setMinOpen(n)}>
              {n}+
            </button>
          ))}
        </div>
      </div>
      <div className="scl">
        <span className="sclab">Credentials VSCS awards</span>
        <div className="chips">
          {TIER_ORDER.map((t) => (
            <button key={t} type="button" className={screenTiers.includes(t) ? 'on' : undefined}
              aria-pressed={screenTiers.includes(t)} onClick={() => toggleTier(t)}>
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="scl">
        <span className="sclab">The obvious</span>
        <div className="chips">
          <button type="button" className={excludeObvious ? 'on' : undefined}
            aria-pressed={excludeObvious} onClick={() => setExcludeObvious((v) => !v)}>
            {excludeObvious ? 'Excluding the 25 largest' : 'Including the 25 largest'}
          </button>
        </div>
      </div>
      <LwPicker value={lw} onChange={setLw} />
    </div>
  );
  const O = SOW.opp;

  // Which credential's list to show. "By credential" was a separate section
  // holding the same scores in a table: the score is the composite, computed
  // across every scored occupation, and picking a credential takes the highest
  // scorers that ask for it. That is a filter, not a second measure -- so it is
  // a control here rather than a page of its own.
  const CREDENTIALS = [{ id: 'all', label: 'All credentials' }].concat(
    TIER_ORDER.filter((t) => O.byTier[t] && O.byTier[t].length).map((t) => ({ id: t, label: t }))
  );
  // Filters narrow the scored list; the composite itself is unchanged. Filtered
  // on the row's own family key -- the rows carry `f`, like every other
  // occupation list on the dashboard.
  const poolFor = (cred) => apply(cred === 'all' ? O.top : O.byTier[cred]);

  return (
    <>
      <VHead
        title="Opportunities"
      >
        Which occupations are worth paying attention to — hiring in numbers, growing, and paying well?
      </VHead>

      <Sections
        id="opportunity"
        active={section}
        items={[
          {
            id: 'highest-scoring',
            label: 'Highest scoring',
            render: () => (
              <>
                <HowTo>
                  One score per occupation, the average of four percentile ranks: how many
                  it employs, how fast it is growing, how heavily it is advertised, and
                  what it pays. Pick a credential to see the highest scorers that ask for
                  it. The score is the same either way — a credential narrows the list, it
                  does not re-grade it.
                </HowTo>
                {/* No filter bar: the pool is already a short list of the highest
                    scorers, and the Show control on the chart is the only narrowing
                    worth offering over it. ActiveFilters stays because a filter set
                    on another tab still applies here -- it appears only when there
                    is one, and lets the reader see and clear it rather than wonder
                    why the chart is short. */}
                <ActiveFilters />
                <Picker id="q5-tier" label="Credential" options={CREDENTIALS}>
                  {(cred) => {
                    const shown = poolFor(cred);
                    return (
                      <Panel
                        title={
                          cred === 'all'
                            ? 'Which occupations combine scale, growth, demand and pay?'
                            : `Which ${cred.toLowerCase()} occupations score highest?`
                        }
                        note={cred === 'all' ? topScoreCredentials(O.top) : null}
                        cap={
                          `Each occupation is ranked against all the others on four things — how many it employs, how fast it is growing, how heavily it is advertised, and what it pays — and the four ranks are averaged. Hover a bar for its four scores.` +
                          (cred === 'all'
                            ? ''
                            : ` These are the highest scorers whose entry credential is ${cred.toLowerCase()}; the score is still the one computed across every occupation, so it can be compared with the others.`)
                        }
                        src={`Vermont occupation data, 2025 · mean of four percentile ranks at ${O.weightEach}% each · occupations with ≥${O.minJobs} jobs (${fmt(O.nEligible)} of 798)`}
                        data={{ cols: scoreCols(), rows: shown, label: 'highest-scoring',
                                initialSort: { k: 'sc', dir: -1 }, unit: 'occupations' }}
                      >
                        <Ranked id="q5-score" rows={shown} show={20}>
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
                        </Ranked>
                      </Panel>
                    );
                  }}
                </Picker>
              </>
            ),
          },
          {
            id: 'program-candidates',
            label: 'Program candidates',
            render: () => (
              <>
                <HowTo>
                  A screen, not a ranking: set the four tests below and the table shows
                  what passes all of them. It is a list of places to look, never a
                  recommendation — the scope of this work stops short of saying whether a
                  program should be created, expanded or cut.
                </HowTo>
              <Panel
                title="Which occupations could VSCS act on?"
                cap={`Occupations that pass four tests at once: at least ${minOpen} openings a year, pay at or above the living wage, and a credential VSCS already awards${excludeObvious ? ', and not one of the 25 largest' : ''}. Signals counts how many of three things an occupation has going for it — openings, advertising and projected growth — each judged against others needing the same credential. Click a row for its occupation group.`}
                src="Vermont occupation data, 2025, against federal completions data, 2024 · thresholds set above · a candidate for investigation, not a recommendation"
                note={screenYield(screened, acted, LC.allOcc.length)}
              >
                {controls}
                <DataTable
                  cols={screenCols()}
                  rows={screened}
                  initialSort={{ k: 'o', dir: -1 }}
                  exportLabel="program-opportunities"
                  rowKey={(r) => r.s}
                  onRowClick={screenDrill}
                  pageSize={30}
                />
              </Panel>
              </>
            ),
          },
          // --- Hidden for now ---------------------------------------------
          // A prose restatement of the Program candidates table.
          // Restore by uncommenting this block and its entry in lib/nav.js.
          // {
          // id: 'read-out',
          // label: 'Read out',
          // render: () => (
          // <Panel
          // title="How would these read out loud?"
          // cap="The same candidates written as you would say them out loud rather than read them off a table, ordered by openings a year. Set the tests on the previous section."
          // src="Generated from the figures in the table · no figure appears here that is not in it"
          // >
          // {acted.length ? (
          // <ol className="narr">
          // {acted.slice(0, 10).map((r) => (
          // <li key={r.s}>{screenNarration(r)}</li>
          // ))}
          // </ol>
          // ) : (
          // <p className="cap">
          // No occupation clears the screen at these criteria. Loosen the minimum
          // openings, add a credential, or include the largest occupations.
          // </p>
          // )}
          // </Panel>
          // ),
          // },

          // --- Hidden for now ---------------------------------------------
          // The same table now sits under the charts it belongs to.
          // Restore by uncommenting this block and its entry in lib/nav.js.
          // {
          // id: 'all-occupations',
          // label: 'All occupations',
          // render: () => (
          // <>
          // <ActiveFilters />
          // <Filters shown={shown.length} total={O.top.length} note="of the 30 highest scoring" pool={O.top} showFamilies />
          // <OccTable lw={lw} />
          // </>
          // ),
          // },

          // --- Hidden for now ---------------------------------------------
          // Methods defines the opportunity index under "What the measures mean".
          // Restore by uncommenting this block and its entry in lib/nav.js.
          // {
          // id: 'how-the-index-is-built',
          // label: 'How the index is built',
          // render: () => (
          // <Callout label="How the index is built">
          // <p>
          // Four components, <N>25%</N> each: employment, projected change 2025&ndash;2030,
          // postings per 100 jobs, and median pay. Each occupation is ranked by percentile
          // within every component and the index is the mean of those four ranks. Only
          // occupations with at least <N>100</N> jobs and a published wage are scored.
          // </p>
          // <p>
          // The four measure different things: their strongest mutual correlation is{' '}
          // <N>0.39</N>, and effective influence spans <N>18.6%</N> to <N>29.4%</N> against a
          // nominal <N>25%</N>. Living-wage ratios and absolute openings are reported per
          // occupation but are not part of the score.
          // </p>
          // </Callout>
          // ),
          // },

        ]}
      />
    </>
  );
}
