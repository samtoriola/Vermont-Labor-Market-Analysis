'use client';

import { useState, useEffect } from 'react';
import { DEFAULT_LW, LC, SERIES_HEX, ORDINAL_HEX, GOOD_HEX, BAD_HEX, lwAnnual } from '@/lib/data';
import { TooltipProvider } from './Tooltip';
import { DrillProvider } from './Drill';
import { FilterProvider } from './FilterContext';
import Overview from './views/Overview';
import Structure from './views/Q1';
import WageQuality from './views/Q2';
import Demand from './views/Q3';
import Pathways from './views/Q4';
import Opportunity from './views/Q5';
import Alignment from './views/Q6';
import Regions from './views/Q7';

const VIEWS = [
  ['overview', 'Overview', Overview],
  ['structure', 'Employment structure', Structure],
  ['wage', 'Wage quality', WageQuality],
  ['demand', 'Demand & growth', Demand],
  ['pathways', 'Pathways', Pathways],
  ['opportunity', 'Opportunities', Opportunity],
  ['alignment', 'VSCS alignment', Alignment],
  ['regions', 'Regions', Regions],
];

function readStored(key, fallback, valid) {
  try {
    const v = localStorage.getItem(key);
    if (v && valid(v)) return v;
  } catch (e) {
    /* blocked storage — use the default */
  }
  return fallback;
}

function writeStored(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch (e) {
    /* non-fatal */
  }
}

export default function Dashboard() {
  const [tab, setTab] = useState('overview');
  const [lw, setLw] = useState(DEFAULT_LW);

  // Restore after mount so server and first client render agree.
  useEffect(() => {
    setTab(readStored('vt-tab', 'overview', (v) => VIEWS.some((x) => x[0] === v)));
    setLw(readStored('vt-lw', DEFAULT_LW, (v) => Object.keys(LC.livingWage).includes(v)));
  }, []);

  function selectTab(id) {
    setTab(id);
    writeStored('vt-tab', id);
  }

  function selectLw(v) {
    setLw(v);
    writeStored('vt-lw', v);
  }

  return (
    <TooltipProvider>
      <DrillProvider>
        <FilterProvider lwAnnual={lwAnnual(lw)}>
        <header className="top">
          <div className="top-in">
            <div className="eyebrow">Strada Education Foundation</div>
            <h1>Vermont Labor Market Overview</h1>
            <p className="sub">
              Employment structure, wage quality, employer demand and education pathways across
              Vermont, with VSCS credential production set against occupational demand.
            </p>
            <nav className="tabs" role="tablist" aria-label="Sections">
              {VIEWS.map(([id, label]) => (
                <button
                  key={id}
                  id={`tab-${id}`}
                  role="tab"
                  aria-selected={tab === id}
                  aria-controls={`view-${id}`}
                  onClick={() => selectTab(id)}
                >
                  {label}
                </button>
              ))}
            </nav>
          </div>
        </header>

        <div className="wrap">
          {VIEWS.map(([id, , View]) => (
            <section
              key={id}
              className="view"
              id={`view-${id}`}
              role="tabpanel"
              aria-labelledby={`tab-${id}`}
              hidden={tab !== id}
            >
              {tab === id ? <View lw={lw} setLw={selectLw} /> : null}
            </section>
          ))}
          <Methods />
        </div>
        </FilterProvider>
      </DrillProvider>
    </TooltipProvider>
  );
}

function Swatches({ items }) {
  return (
    <div className="swatches">
      {items.map(([hex, label]) => (
        <span key={hex + label}>
          <i style={{ background: hex }} />
          {label} {hex}
        </span>
      ))}
    </div>
  );
}

function Methods() {
  return (
    <footer className="meth">
      <h3>Methodology, definitions &amp; limitations</h3>
      <div className="mgrid">
        <div>
          <h4>Sources</h4>
          <p>
            <strong>Lightcast</strong> Vermont exports — 798 detailed occupations with annual wage
            percentiles and 2021–2025 openings, 947 NAICS industries, 694 occupations of job
            postings (Jan 2021 – Jan 2026). <strong>CPS</strong> IPUMS basic monthly, Vermont,
            2021–2025. <strong>IPEDS</strong> 2024 completions for CCV and Vermont State
            University. <strong>ACS</strong> 2016–2020 5-year county tables.{' '}
            <strong>MIT Living Wage</strong> 2025.
          </p>
        </div>

        <div>
          <h4>Jobs vs workers</h4>
          <p>
            Lightcast counts <em>jobs</em> and the credential a job asks for. CPS counts{' '}
            <em>employed residents</em> and the credential they hold — 326,582 jobs against 335,775
            employed. The ~3% gap is definitional, so compare shares, not levels. CPS and ACS
            attainment differ by about 6 points too: use CPS for direction over time, ACS for
            levels, never both in one exhibit.
          </p>
        </div>

        <div>
          <h4>Openings</h4>
          <p>
            Lightcast’s <code>2021–2025 Openings</code> (195,571) ÷ 4 = 48,893 a year, 15.0% of
            employment. The divisor matches how Lightcast computes the paired change figure. Not the
            same as <code>Separations</code> (202,870), which includes job-to-job transfers and so
            measures churn rather than hiring need.
          </p>
        </div>

        <div>
          <h4>Wage percentiles</h4>
          <p>
            Annual figures as supplied, all 798 occupations; 16 with zero earnings are excluded
            (0.00% of jobs). The percentile ladder shows one occupation’s own published
            percentiles and mean. Group figures — family, credential tier, size tier — are the
            employment-weighted mean of their occupations’ percentiles, so they describe range
            faithfully but are not exact group quantiles.
          </p>
        </div>

        <div>
          <h4>Living wage is a setting</h4>
          <p>
            MIT’s Vermont figures span $17.06/hr (two adults working, no children) to $63.91/hr (one
            adult, two children). The default is <strong>$23.95</strong> — one adult, no children —
            annualised at 2,080 hours. Across counties the one-adult figure ranges $21.79–$25.85.
            Every wage-quality number moves with this choice.
          </p>
        </div>

        <div>
          <h4>Rates on small bases</h4>
          <p>
            Lightcast models employment to a fraction of a job, so any rate with a tiny
            denominator is noise. Gambling Managers carries <strong>0.005 jobs</strong> against a
            projected gain of 1.0, which computes as 19,390% growth; Bailiffs goes 0.1 to 55.9
            jobs, which computes as +54,601%. Projected growth, observed change and turnover are
            therefore left blank unless their own denominator carries at least{' '}
            <strong>10 jobs</strong>. That suppresses about 120 of 796 occupations per measure,
            together <strong>0.11%</strong> of state employment, and caps projected growth at
            29.1% and observed change at 1,118% — both real moves on small bases. A blank means
            the base was too small to support a percentage, not that the figure is zero.
          </p>
        </div>

        <div>
          <h4>Opportunity score</h4>
          <p>
            Mean of four percentile ranks, 25% each: employment, projected growth, postings per 100
            jobs, median pay. Two candidates were dropped after measurement — a living-wage ratio
            (rank-identical to pay, r = 1.000) and openings intensity (−0.68 against pay,
            contributing −4.7% of variance). The four survivors correlate at most 0.39.
          </p>
        </div>

        <div>
          <h4>Program alignment</h4>
          <p>
            CIP-to-SOC is many-to-many, so each program’s completions are divided across its
            linked occupations in proportion to those occupations’ Vermont employment. All 149
            VSCS programs and 1,983 completions matched the crosswalk, and the total is preserved.
            That weighting moves 32.5% of completions relative to a flat split — it is a model of
            where graduates go, not an observation. 21 programs link only to occupations with no
            Vermont employment and fall back to an equal split. One year; counts credentials, not
            people; silent on whether graduates stay in Vermont.
          </p>
        </div>

        <div>
          <h4>CPS precision</h4>
          <p>
            October 2025 is missing nationally, so 2025 is an 11-month average. Vermont weights are
            near-uniform (Kish 0.94) and month-to-month spread matches the simple-random-sample
            expectation, so intervals assume a design effect near 1. Across 2021–2025 Vermont has
            80,569 person-month records but 16,887 distinct people.
          </p>
        </div>

        <div>
          <h4>Colour coding</h4>
          <p>Colour follows the entity, never its rank. Ordered measures use a single hue.</p>
          <Swatches
            items={[
              [GOOD_HEX, 'At/above living wage'],
              [BAD_HEX, 'Below living wage'],
            ]}
          />
          <Swatches items={SERIES_HEX.map((h, i) => [h, `Series ${i + 1}`])} />
          <Swatches
            items={[
              [ORDINAL_HEX[0], 'Ramp low'],
              [ORDINAL_HEX[4], 'Ramp high'],
            ]}
          />
        </div>

        <div>
          <h4>Not covered</h4>
          <p>
            Demand by county — both Lightcast exports are statewide. VSCS program inventory and
            enrolment, so capacity is invisible. Graduate retention and destination. And programs
            serving public or civic need that demand data does not capture: absence of a signal here
            is not evidence of low value.
          </p>
        </div>
      </div>
    </footer>
  );
}
