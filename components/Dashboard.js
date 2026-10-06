'use client';

import { useState, useEffect } from 'react';
import { DEFAULT_LW, LC, lwAnnual } from '@/lib/data';
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
import Opportunities8 from './views/Q8';
import About from './views/About';
import Methods from './views/Methods';

const VIEWS = [
  ['overview', 'Overview', Overview],
  ['structure', 'Employment structure', Structure],
  ['wage', 'Wage quality', WageQuality],
  ['demand', 'Demand & growth', Demand],
  ['pathways', 'Pathways', Pathways],
  ['opportunity', 'Opportunities', Opportunity],
  ['alignment', 'VSCS alignment', Alignment],
  ['regions', 'Regions', Regions],
  ['implications', 'Program opportunities', Opportunities8],
  ['about', 'About', About],
  ['methods', 'Methods & limits', Methods],
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
        </div>
        </FilterProvider>
      </DrillProvider>
    </TooltipProvider>
  );
}
