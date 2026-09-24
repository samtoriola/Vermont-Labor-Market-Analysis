'use client';

// Section: Regional variation
import { useState } from 'react';
import { SOW } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Callout, Panel, Table, VHead, N } from '../ui';
import VermontMap from '../VermontMap';

export default function Q7() {
  const [metric, setMetric] = useState('ba');
  const [sel, setSel] = useState(null);

  const R = SOW.regions;
  const byPop = R.slice().sort((a, b) => b.pop - a.pop);
  const picked = sel ? R.find((r) => r.c === sel) : null;
  const wBa = R.reduce((a, r) => a + r.ba * r.pop, 0) / R.reduce((a, r) => a + r.pop, 0);

  return (
    <>
      <VHead title="Regional variation">
        How opportunity differs across Vermont’s 14 counties — attainment, earnings and the local
        cost floor.
      </VHead>

      <Panel
        title="Vermont by county"
        cap="Switch the shading metric, then click a county — on the map or in the list — to pin it."
        src="ACS 2016–2020 5-year · MIT Living Wage 2025 · outlines from Census TIGER, simplified"
      >
        <VermontMap
          regions={R}
          metric={metric}
          setMetric={setMetric}
          selected={sel}
          onSelect={setSel}
        />
      </Panel>

      {picked ? (
        <Panel
          title={picked.c + ' County'}
          cap="Pinned from the map. Click it again, or choose another, to change this."
          src="ACS 2016–2020 5-year · MIT Living Wage 2025"
        >
          <div className="dstats">
            <div className="dstat">
              <div className="k">Population</div>
              <div className="v">{fmt(picked.pop)}</div>
            </div>
            <div className="dstat">
              <div className="k">BA+ 25–64</div>
              <div className="v">{picked.ba}%</div>
            </div>
            <div className="dstat">
              <div className="k">Median income</div>
              <div className="v">{money(picked.inc)}</div>
            </div>
            <div className="dstat">
              <div className="k">Living wage /hr</div>
              <div className="v">${picked.lwH.toFixed(2)}</div>
            </div>
            <div className="dstat">
              <div className="k">Income ÷ LW</div>
              <div className="v">{picked.incLw}×</div>
            </div>
          </div>
          <p className="cap" style={{ margin: 0 }}>
            Vermont for comparison: <N>{wBa.toFixed(1)}%</N> BA+ (population-weighted),
            living wage <N>$23.95</N>/hr statewide.
          </p>
        </Panel>
      ) : null}

      <Panel
        title="All 14 counties"
        cap="Click a row to pin that county on the map above."
        src="ACS 2016–2020 5-year · MIT Living Wage 2025"
      >
        <Table
          cols={[
            'County',
            'Population',
            'BA+ 25–64',
            'Median income',
            'Living wage /hr',
            'Living wage /yr',
            'Income ÷ LW',
          ]}
          rows={byPop.map((r) => ({
            onClick: () => setSel(sel === r.c ? null : r.c),
            cells: [
              r.c,
              fmt(r.pop),
              r.ba + '%',
              money(r.inc),
              '$' + r.lwH.toFixed(2),
              money(r.lwA),
              r.incLw + '×',
            ],
          }))}
        />
      </Panel>

      <Callout label="What this map cannot show">
        <p>
          Demand is statewide only. The Lightcast occupation and postings exports carry no county
          breakdown, and CPS resolves Vermont to metro/non-metro and nothing finer — so
          occupational demand and occupation-specific wage premiums by county are absent. Lightcast
          Core LMI covers all 14 counties and would close that gap.
        </p>
        <p>
          Two caveats on what is here: county lines and the ACS PUMA areas used for microdata do
          not nest, so a demand-side regional view and a microdata attainment view cannot yet share
          a map. And median <em>household</em> income against a single-adult wage floor is
          indicative, not like-for-like.
        </p>
      </Callout>
    </>
  );
}
