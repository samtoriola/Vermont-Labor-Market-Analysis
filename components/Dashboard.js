'use client';

import { useState, useEffect } from 'react';
import { DEFAULT_LW, LC } from '@/lib/data';
import { TooltipProvider } from './Tooltip';
import Overview from './views/Overview';
import Q1 from './views/Q1';
import Q2 from './views/Q2';
import Q3 from './views/Q3';
import Q4 from './views/Q4';
import Q5 from './views/Q5';
import Q6 from './views/Q6';
import Q7 from './views/Q7';
import Q8 from './views/Q8';

const VIEWS = [
  ['overview', 'Overview', null, Overview],
  ['q1', 'Distribution', 'Q1', Q1],
  ['q2', 'Size & wage quality', 'Q2', Q2],
  ['q3', 'Demand & growth', 'Q3', Q3],
  ['q4', 'Pathways', 'Q4', Q4],
  ['q5', 'Opportunities', 'Q5', Q5],
  ['q6', 'VSCS alignment', 'Q6', Q6],
  ['q7', 'Regions', 'Q7', Q7],
  ['q8', 'Implications', 'Q8', Q8],
];

function readStored(key, fallback, isValid) {
  try {
    const v = localStorage.getItem(key);
    if (v && isValid(v)) return v;
  } catch (e) {
    /* private mode, blocked storage — fall through */
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
  // Start from the defaults so server and first client render agree, then
  // restore the viewer's last choices after mount.
  const [tab, setTab] = useState('overview');
  const [lw, setLw] = useState(DEFAULT_LW);

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
      <header className="top">
        <div className="top-in">
          <div className="eyebrow">Strada Education Foundation · VSCS Program Alignment</div>
          <h1>Vermont Labor Market Overview</h1>
          <p className="sub">
            All eight research questions from the scope of work. Lightcast 2025 occupation, industry
            and postings data for levels, wages and projections; CPS microdata 2021&ndash;2025 for
            the employment base and worker attainment; IPEDS 2024 completions for VSCS program
            alignment; ACS and MIT living wage for regional comparison.
          </p>
          <div className="mock-flag">
            Mockup for review · benchmarks, weights and regional definitions not yet set
          </div>
          <nav className="tabs" role="tablist" aria-label="Research questions">
            {VIEWS.map(([id, label, qn]) => (
              <button
                key={id}
                id={`tab-${id}`}
                role="tab"
                aria-selected={tab === id}
                aria-controls={`view-${id}`}
                onClick={() => selectTab(id)}
              >
                {qn ? <span className="qn">{qn}</span> : null}
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <div className="wrap">
        {VIEWS.map(([id, , , View]) => (
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
    </TooltipProvider>
  );
}

function Methods() {
  return (
    <footer className="meth">
      <h3>Methods, definitions &amp; limitations</h3>
      <div className="mgrid">
        <div>
          <h4>Sources</h4>
          <p>
            Lightcast Vermont exports: occupation table (798 detailed SOC, with annual wage
            percentiles and 2021&ndash;2025 openings), industry table (947 six-digit NAICS),
            job-postings table (694 SOC, window Jan 2021 &ndash; Jan 2026). CPS: IPUMS basic
            monthly, <code>monthly_cps.cps</code>, Vermont, 2021&ndash;2025. VSCS completions:{' '}
            <code>ipeds.2024_Completions_AwardsByCIP_C2024_A</code> for Community College of Vermont
            (230861) and Vermont State University (231165), mapped through{' '}
            <code>cip_soc_crosswalk.cip2020_soc2018_crosswalk</code>. Regional attainment and
            income: <code>census_bureau_acs.county_2020_5yr</code>. Benchmark:{' '}
            <code>sandbox.mit_living_wage_2025</code>.
          </p>
        </div>
        <div>
          <h4>The two main sources measure different things</h4>
          <p>
            Lightcast counts <em>jobs</em> and assigns each occupation a typical entry credential
            &mdash; a property of the job. CPS counts <em>employed residents</em> and records the
            credential each person holds. Lightcast reports 326,582 jobs; CPS reports 335,775
            employed. The ~3% gap is definitional. Compare shares, never levels.
          </p>
        </div>
        <div>
          <h4>Openings, and the one assumption in them</h4>
          <p>
            Openings are Lightcast&rsquo;s own <code>2021 - 2025 Openings</code> column &mdash;
            195,571 across the window &mdash; divided by 4 to give 48,893 a year, or 15.0% of
            employment. The divisor of 4 matches how Lightcast computes{' '}
            <code>2021 - 2025 Change</code> (an endpoint difference across four intervals). If that
            window is meant to be inclusive of five years, every openings figure scales down by a
            fifth.
          </p>
          <p>
            This is not the same as <code>2025 Separations</code> (202,870, or 62.1% of employment),
            which includes job-to-job transfers and so measures churn rather than hiring need.
          </p>
        </div>
        <div>
          <h4>Two different time windows are in play</h4>
          <p>
            Occupation-level figures are window-consistent: <code>2021 Jobs</code> to{' '}
            <code>2025 Jobs</code>, matching the CPS period. Forward projections run
            2025&ndash;2030. The <strong>industry</strong> export, however, carries only 2001 and
            2025 job columns, so no 2021 sector baseline exists &mdash; sector figures are 2025
            levels only, and sector change over the study window is deliberately omitted.
          </p>
        </div>
        <div>
          <h4>Wage percentiles, and what the group boxes mean</h4>
          <p>
            Percentiles come from the updated Lightcast occupation export as <em>annual</em> figures
            (10th, 25th, 75th, 90th plus the median), so no annualisation is applied. All 798
            occupations carry values; 16 have zero earnings and are excluded, together accounting
            for 0.00% of jobs. All 782 priced occupations are monotonic across the five percentiles.
          </p>
          <p>
            Occupation-level boxes are true percentiles. Boxes for a <em>group</em> &mdash; a family,
            credential tier or size tier &mdash; are the employment-weighted mean of the constituent
            occupations&rsquo; percentiles, not a pooled distribution. Do not quote a group&rsquo;s
            10th percentile as a population figure.
          </p>
        </div>
        <div>
          <h4>Living wage is a choice, not a constant</h4>
          <p>
            MIT Living Wage 2025 for Vermont ranges from $17.06/hr (two adults both working, no
            children) to $63.91/hr (one adult, two children). The default here is $23.95 &mdash; one
            adult, no children. Across the 14 counties the one-adult figure ranges
            $21.79&ndash;$25.85. SOW section 7 leaves this selection to VSCS; every wage-quality
            figure moves with it.
          </p>
        </div>
        <div>
          <h4>The opportunity score is a default, not a decision</h4>
          <p>
            Question 5&rsquo;s composite is the mean of <strong>four</strong> percentile ranks at{' '}
            <strong>25% each</strong>: employment, projected growth, postings per 100 jobs, and
            median pay. It started as six. <em>Earnings relative to the living wage</em> was dropped
            as rank-identical to median pay (r = 1.000, since the benchmark is a constant).{' '}
            <em>Openings</em> was dropped next: as an absolute count it correlated 0.92 with
            employment, and rebased per 100 jobs it became a turnover measure correlating
            &minus;0.68 with pay, contributing &minus;4.7% of composite variance. The four survivors
            have a maximum mutual correlation of 0.39 and effective influence of
            18.6%&ndash;29.4% against the nominal 25%.
          </p>
        </div>
        <div>
          <h4>VSCS alignment rests on an allocation assumption</h4>
          <p>
            CIP-to-SOC is many-to-many, so each program&rsquo;s completions are split <em>equally</em>{' '}
            across its linked occupations. All 149 VSCS programs and all 1,983 completions matched
            the crosswalk, so nothing is dropped &mdash; but the split is an assumption, and a
            program whose graduates concentrate in one occupation is understated. It is a single year
            and counts credentials rather than people.
          </p>
        </div>
        <div>
          <h4>CPS precision and the 2025 gap</h4>
          <p>
            October 2025 CPS is absent nationally, so 2025 is an 11-month average. Vermont CPS
            weights are near-uniform (Kish efficiency 0.94) and observed month-to-month spread
            matches the simple-random-sample expectation, so intervals assume a design effect near 1.
            Over 2021&ndash;2025 Vermont has 80,569 person-month records but only 16,887 distinct
            people.
          </p>
        </div>
        <div>
          <h4>Do not mix CPS and ACS levels</h4>
          <p>
            CPS puts Vermont BA+ attainment among adults 25+ at 48.0%; ACS 2023 puts it at 41.9%
            &plusmn;2.0. The 6-point gap is measurement difference, not noise. Use CPS for direction
            over time and ACS for levels &mdash; never both in one exhibit.
          </p>
        </div>
        <div>
          <h4>What is still missing</h4>
          <p>
            Research question 7 is half-answered. Regional <em>attainment</em> and <em>wage
            sufficiency</em> are here by county, but occupational <em>demand</em> and
            occupation-specific <em>wage premiums</em> by region are not: both Lightcast exports are
            statewide and CPS resolves Vermont only to metro/non-metro. Lightcast Core LMI covers all
            14 Vermont counties and would close it.
          </p>
          <p>
            Also absent: VSCS programme inventory and enrolment, graduate retention and destination,
            and any measure of programmes serving public or civic need that demand data does not
            capture &mdash; which SOW section 4D asks for explicitly and which should not be inferred
            from a low score here.
          </p>
        </div>
      </div>
    </footer>
  );
}
