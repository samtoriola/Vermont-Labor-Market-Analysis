'use client';

// Section: Regional variation
import { useState } from 'react';
import { CTY, SOW, lwAnnual } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { countyCols, countyMixCols } from '@/lib/tables';
import { Callout, HowTo, Legend, Panel, Picker, VHead, LwPicker, N } from '../ui';
import { RankedBars } from '../charts';
import { Heatmap, HEAT_STEPS, HEAT_COLORS, HEAT_PRINT_FROM } from '../heatmap';
import VermontMap from '../VermontMap';
import Sections from '../Sections';
import {
  countySpread, countyJobs, countyPay, countyChange, countyMix,
} from '@/lib/insight';

// Callout below is used only by the section(s) hidden further down. Kept
// imported so restoring one stays a single edit.

const MEASURES = [
  { id: 'jobs', label: 'Jobs' },
  { id: 'pay', label: 'Typical pay' },
  { id: 'change', label: 'Change since ' + CTY.base },
  { id: 'mix', label: 'What it specialises in' },
];

export default function Q7({ lw, setLw, section }) {
  const [metric, setMetric] = useState('ba');
  const [sel, setSel] = useState(null);
  const LWA = lwAnnual(lw);

  const R = SOW.regions;
  const C = CTY.counties;
  const ST = CTY.state;
  const thin = C.filter((r) => r.thin);
  const covered = (C.reduce((a, r) => a + r.emp, 0) / ST.emp) * 100;

  // The residents and the jobs, joined on the county so one table can carry
  // both. They are different measurements of the same place, not two halves of
  // one -- which is why the column headings say which is which.
  const byName = {};
  C.forEach((r) => {
    byName[r.c] = r;
  });
  const rows = R.map((r) => ({ ...r, ...(byName[r.c] || {}) })).sort((a, b) => b.pop - a.pop);
  const picked = sel ? rows.filter((r) => r.c === sel)[0] : null;
  const wBa = R.reduce((a, r) => a + r.ba * r.pop, 0) / R.reduce((a, r) => a + r.pop, 0);

  const pick = (c) => setSel(sel === c ? null : c);

  // Shown under the map and under the ranked chart: a pin set from either should
  // stay visible wherever it was set.
  const pinned = () =>
    picked ? (
      <Panel
        title={picked.c + ' County'}
        cap="Pinned from the map, a bar or the county list. Click it again, or choose another, to change this."
        src={`County survey data, 2016–2020 · county employment and pay ${CTY.year} · living-wage benchmark 2025`}
      >
        <div className="dstats">
          <div className="dstat">
            <div className="k">Jobs in the county</div>
            <div className="v">{picked.emp ? fmt(picked.emp) : '—'}</div>
          </div>
          <div className="dstat">
            <div className="k">Typical job pays</div>
            <div className="v">{picked.med ? money(picked.med) : '—'}</div>
          </div>
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
            <div className="k">Income ÷ LW</div>
            <div className="v">{picked.incLw}×</div>
          </div>
        </div>
        <p className="cap" style={{ margin: 0 }}>
          Vermont for comparison: <N>{wBa.toFixed(1)}%</N> BA+ (population-weighted),
          a typical job at <N>{money(ST.med)}</N>, living wage <N>$23.95</N>/hr statewide.
        </p>
      </Panel>
    ) : null;

  // Every county-and-family pair, the figures behind the grid. One row each
  // rather than a 22-column table nobody can read on a laptop.
  const mixRows = [];
  C.forEach((r) =>
    CTY.famOrder.forEach((f) => {
      mixRows.push({
        c: r.c, f, jobs: r.jobs[f], mix: r.mix[f], st: ST.share[f], lq: r.lq[f],
      });
    })
  );

  const bar = (r, value, opts) => ({
    label: r.c,
    value,
    onClick: () => pick(r.c),
    active: sel === r.c,
    big: [[fmt(r.emp), 'Jobs in the county']],
    extra: [
      ['Typical job pays', money(r.med)],
      ['Change since ' + CTY.base, (r.chg > 0 ? '+' : '') + r.chg + '%'],
      ['Share of state employment', ((r.emp / ST.emp) * 100).toFixed(1) + '%'],
      ...(r.thin ? [['Note', 'One of the two smallest counties']] : []),
    ],
    ...opts,
  });

  // Vermont as a grey reference bar rather than a fifteenth county, and only on
  // the measures where it is a peer of the counties rather than their sum. A
  // state median sits among the county medians and can be read against them; a
  // state total is three times the largest county, so drawing it squeezes all
  // fourteen into the left third of the plot to make a point the caption and
  // the read-out both make in words.
  const stateBar = (value, opts) => ({
    label: 'Vermont',
    value,
    color: '--ink-3',
    extra: [
      ['Counties shown', fmt(C.length)],
      ['They account for', covered.toFixed(1) + '% of state jobs'],
    ],
    ...opts,
  });

  const thinLine = thin.length
    ? ` ${thin.map((r) => r.c).join(' and ')} hold under ${fmt(CTY.thinFloor)} jobs each, so their figures move on very little.`
    : '';

  const measure = {
    jobs: {
      title: 'How many jobs does each county hold?',
      note: countyJobs(C, ST),
      cap: `Every county, largest first. Vermont as a whole holds ${fmt(ST.emp)}, which is not drawn here: a bar three times the longest would leave the other thirteen unreadable. The counties account for ${covered.toFixed(1)}% of it, the rest being employment reported without a county.`,
      src: `Vermont employment by county, ${CTY.year} · employees · click a bar to pin the county`,
      chart: (
        <RankedBars
          rows={C.slice()
            .sort((a, b) => b.emp - a.emp)
            .map((r) => bar(r, r.emp, { color: '--s1' }))}
          opts={{
            labelWidth: 150,
            valueLabel: 'Jobs',
            clickHint: 'Click to pin this county',
            aria: 'Employment by county',
          }}
        />
      ),
    },

    pay: {
      lw: true,
      title: 'What does a typical job pay in each county?',
      note: countyPay(C, ST),
      cap: `The midpoint job in the county, which is not the midpoint worker — people commute, and the Workers tab answers that one. Green clears the living wage, amber does not.${thinLine}`,
      src: `Vermont occupation pay by county, ${CTY.year} · weighted by employment across every detailed occupation · annualised at 2,080 hours`,
      chart: (
        <RankedBars
          rows={C.filter((r) => r.med)
            .sort((a, b) => b.med - a.med)
            .map((r) => bar(r, r.med, { color: r.med >= LWA ? '--s3' : '--s2' }))
            .concat(stateBar(ST.med))}
          opts={{
            money: true,
            labelWidth: 150,
            rule: LWA,
            ruleLabel: 'Living wage',
            valueLabel: 'Typical pay',
            clickHint: 'Click to pin this county',
            aria: 'Typical pay by county',
          }}
        />
      ),
    },

    change: {
      title: `Which counties hold more work than in ${CTY.base}?`,
      note: countyChange(C, CTY.base, CTY.year),
      cap: `Change in total employment over the ${CTY.year - CTY.base} years to ${CTY.year}. Green grew, amber shrank.${thinLine}`,
      src: `Vermont employment by county, ${CTY.base} and ${CTY.year} · employees`,
      chart: (
        <RankedBars
          rows={C.filter((r) => r.chg !== null && r.chg !== undefined)
            .sort((a, b) => b.chg - a.chg)
            .map((r) => bar(r, r.chg, { color: r.chg >= 0 ? '--s3' : '--s2', mode: 'pct' }))}
          opts={{
            mode: 'pct',
            signed: true,
            labelWidth: 150,
            valueLabel: 'Change in jobs',
            clickHint: 'Click to pin this county',
            aria: 'Change in county employment',
          }}
        />
      ),
    },

    mix: {
      title: 'What is each county actually specialised in?',
      note: countyMix(C, CTY.famOrder),
      cap: `Each cell is the county's share of its own jobs in a kind of work, against Vermont's share of the same work. 1.0 means the county looks exactly like the state, and the shading changes colour there. The figure is printed on the darkest step, from ${HEAT_PRINT_FROM}× up. It is a ratio of shares and says nothing about size, so hover for the job count behind it.${thinLine} Those two are outlined.`,
      src: `Vermont occupation data by county, ${CTY.year} · share of county employment against share of state employment · counties ordered by employment`,
      chart: (
        <>
          <Legend labels={HEAT_STEPS} colors={HEAT_COLORS} />
          <Heatmap
            cols={C.map((r) => ({ k: r.c, label: r.c, thin: r.thin }))}
            rows={CTY.famOrder.map((f) => ({ k: f, label: f }))}
            value={(ck, rk) => {
              const r = byName[ck];
              if (!r || r.lq[rk] === null || r.lq[rk] === undefined) return null;
              return {
                v: r.lq[rk],
                extra: [
                  ['Jobs here', fmt(r.jobs[rk])],
                  ['Share of the county', r.mix[rk].toFixed(1) + '%'],
                  ['Share of Vermont', ST.share[rk].toFixed(1) + '%'],
                ],
              };
            }}
            opts={{
              valueLabel: 'Times the state share',
              thinNote: 'One of the two smallest counties — thin figures',
              aria: 'Occupational concentration by county',
            }}
          />
        </>
      ),
    },
  };

  return (
    <>
      <VHead title="Regional variation">
        How does labor market opportunity vary across Vermont’s regions, including differences in occupational demand, wage sufficiency, educational attainment, and occupation-specific wage premiums?
      </VHead>

      <Sections
        id="regions"
        active={section}
        items={[
          {
            id: 'map',
            label: 'County map',
            render: () => (
              <>
                <HowTo>
                  Choose what the shading shows, then click a county to pin its figures
                  below. The figures under the map carry every county on both counts — the
                  jobs located there, and the people who live there.
                </HowTo>
                <Panel
                  title="How does opportunity differ across Vermont’s counties?"
                  note={countySpread(R)}
                  cap="Choose what the shading shows, then click a county to pin it. Clicking a row in the figures pins it too."
                  src={`County survey data, 2016–2020 · county employment and pay ${CTY.year} · living-wage benchmark 2025 · simplified county outlines`}
                  data={{ cols: countyCols(), rows, label: 'counties',
                          initialSort: { k: 'emp', dir: -1 }, unit: 'counties',
                          onRowClick: (r) => pick(r.c),
                          note: 'Jobs and typical pay are the county’s workplaces; population, attainment and income are its residents. Click a row to pin that county.' }}
                >
                  <VermontMap
                    regions={R}
                    metric={metric}
                    setMetric={setMetric}
                    selected={sel}
                    onSelect={setSel}
                  />
                </Panel>
                {pinned()}
              </>
            ),
          },
          {
            id: 'counties',
            label: 'Counties compared',
            render: () => (
              <>
                <HowTo>
                  One measure at a time across all fourteen counties. Pick the measure and
                  the chart, the line under it and the figures all follow. Click any bar to
                  pin that county.
                </HowTo>
                {/* No top / bottom control: fourteen bars already fit, and the
                    grid has to show every county or the comparison it draws is
                    against a state the columns no longer cover. */}
                <Picker id="q7-cty" label="Measure" options={MEASURES}>
                  {(m) => {
                    const v = measure[m];
                    return (
                      <>
                        {v.lw ? <LwPicker value={lw} onChange={setLw} /> : null}
                        <Panel
                          title={v.title}
                          note={v.note}
                          cap={v.cap}
                          src={v.src}
                          data={
                            m === 'mix'
                              ? { cols: countyMixCols(), rows: mixRows, label: 'county-concentration',
                                  initialSort: { k: 'lq', dir: -1 }, unit: 'county and family pairs' }
                              : { cols: countyCols(), rows, label: 'counties-compared',
                                  initialSort: { k: 'emp', dir: -1 }, unit: 'counties',
                                  onRowClick: (r) => pick(r.c) }
                          }
                        >
                          {v.chart}
                        </Panel>
                        {m === 'mix' ? null : pinned()}
                      </>
                    );
                  }}
                </Picker>
              </>
            ),
          },
          // --- Hidden for now ---------------------------------------------
          // Moved into the "Not covered" list on Methods.
          // Restore by uncommenting this block and its entry in lib/nav.js.
          // {
          // id: 'limits',
          // label: 'What this cannot show',
          // render: () => (
          // <Callout label="What this map cannot show">
          // <p>
          // County lines and the ACS PUMA areas used for microdata do not nest, so a
          // demand-side regional view and a microdata attainment view cannot yet share a
          // map. And median <em>household</em> income against a single-adult wage floor is
          // indicative, not like-for-like.
          // </p>
          // </Callout>
          // ),
          // },

        ]}
      />
    </>
  );
}
