'use client';

import { useState } from 'react';
import { LC, TIER_ORDER, lwAnnual, occByFamily } from '@/lib/data';
import { opportunityScreen, screenCols, SCREEN_TIERS, SUPPLY } from '@/lib/screen';
import { fmt, money } from '@/lib/format';
import { Panel, VHead, LwPicker } from '../ui';
import { useDrill, occDrill } from '../Drill';
import DataTable from '../DataTable';
import Sections from '../Sections';
import { screenYield, screenNarration } from '@/lib/insight';

const OPEN_STEPS = [25, 50, 100];

export default function Q8({ lw, setLw }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();

  const [minOpen, setMinOpen] = useState(50);
  const [tiers, setTiers] = useState(SCREEN_TIERS);
  const [excludeObvious, setExcludeObvious] = useState(true);

  const rows = opportunityScreen({ lwAnnual: LWA, minOpen, tiers, excludeObvious });
  const acted = rows.filter((r) => r.nSignals >= 2 && r.supply !== SUPPLY.established);

  const toggleTier = (t) =>
    setTiers((cur) => (cur.includes(t) ? cur.filter((x) => x !== t) : cur.concat(t)));

  const drill = (r) =>
    open(
      occDrill({
        label: 'Occupational family',
        title: r.f,
        cap: `Opened from ${r.n}. Every occupation in this family.`,
        occ: occByFamily(r.f),
        lwAnnual: LWA,
      })
    );

  return (
    <>
      <VHead title="Program opportunities">
        What findings have the greatest implications for VSCS program planning, including
        opportunities to strengthen, expand, develop, reposition, or further evaluate specific
        program areas?
      </VHead>

      <LwPicker value={lw} onChange={setLw} />

      <div className="panel screenctl">
        <div className="scl">
          <span className="sclab">Minimum annual openings</span>
          <div className="chips">
            {OPEN_STEPS.map((n) => (
              <button
                key={n}
                type="button"
                className={n === minOpen ? 'on' : undefined}
                aria-pressed={n === minOpen}
                onClick={() => setMinOpen(n)}
              >
                {n}+
              </button>
            ))}
          </div>
        </div>

        <div className="scl">
          <span className="sclab">Credentials VSCS awards</span>
          <div className="chips">
            {TIER_ORDER.map((t) => (
              <button
                key={t}
                type="button"
                className={tiers.includes(t) ? 'on' : undefined}
                aria-pressed={tiers.includes(t)}
                onClick={() => toggleTier(t)}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <div className="scl">
          <span className="sclab">The obvious</span>
          <div className="chips">
            <button
              type="button"
              className={excludeObvious ? 'on' : undefined}
              aria-pressed={excludeObvious}
              onClick={() => setExcludeObvious((v) => !v)}
            >
              {excludeObvious ? 'Excluding the 25 largest' : 'Including the 25 largest'}
            </button>
          </div>
        </div>

        <p className="cap" style={{ margin: '4px 0 0' }}>
          {fmt(rows.length)} of {fmt(LC.allOcc.length)} occupations clear the screen;{' '}
          {fmt(acted.length)} of those show movement on at least two signals and are not
          already well supplied.
        </p>
      </div>

      <Sections
        id="opportunities"
        items={[
          {
            id: 'candidates',
            label: 'Candidates',
            render: () => (
              <Panel
                title="Which occupations could VSCS act on?"
                cap={`Occupations clearing all four tests: at least ${minOpen} annual openings, pay at or above the living wage, a credential VSCS awards${excludeObvious ? ', and not among the 25 largest' : ''}. Signals count how many of three movements the occupation shows — openings, advertised demand and projected growth — each ranked within its own credential tier. Click a row for its occupational family.`}
                src="Lightcast occupations × IPEDS 2024 completions via cip2020_soc2018 · thresholds set above · a candidate for investigation, not a recommendation"
                note={screenYield(rows, acted, LC.allOcc.length)}
              >
                <DataTable
                  cols={screenCols()}
                  rows={rows}
                  initialSort={{ k: 'o', dir: -1 }}
                  exportLabel="program-opportunities"
                  rowKey={(r) => r.s}
                  onRowClick={drill}
                  pageSize={30}
                />
              </Panel>
            ),
          },
          {
            id: 'narrated',
            label: 'Read out',
            render: () => (
              <Panel
                title="How would these read out loud?"
                cap="The same rows, stated as they would be said over a slide rather than read off a table. Ordered by annual openings."
                src="Generated from the figures in the table · no figure appears here that is not in it"
              >
                {acted.length ? (
                  <ol className="narr">
                    {acted.slice(0, 10).map((r) => (
                      <li key={r.s}>{screenNarration(r)}</li>
                    ))}
                  </ol>
                ) : (
                  <p className="cap">
                    No occupation clears the screen at these thresholds. Loosen the minimum
                    openings, add a credential tier, or include the largest occupations.
                  </p>
                )}
              </Panel>
            ),
          },
          {
            id: 'how',
            label: 'How this screen works',
            render: () => (
              <Panel title="How this screen works">
                <p className="lede">
                  Four tests, all stated above and all adjustable: enough annual openings to
                  justify a program, pay at or above the chosen self-sufficiency benchmark, a
                  credential VSCS actually awards, and — optionally — not one of the 25
                  occupations everyone already names.
                </p>
                <p className="lede">
                  The three movement signals are ranked <strong>within</strong> each credential
                  tier, never across the whole set. Median advertised demand runs about 65
                  postings per 100 jobs at high school against 161 at bachelor&rsquo;s, because
                  trades are not advertised online at white-collar rates. A single threshold
                  would read as a demand test and act as a credential filter, removing the
                  sub-baccalaureate occupations VSCS is best placed to serve.
                </p>
                <p className="lede">
                  Pipeline compares VSCS completions allocated to each occupation against its
                  annual openings. That allocation is a model of where graduates go, not an
                  observation of it; the method is on the VSCS alignment tab. A row here is a
                  candidate for investigation, not a recommendation.
                </p>
              </Panel>
            ),
          },
        ]}
      />
    </>
  );
}
