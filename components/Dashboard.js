'use client';

import { useState, useEffect, useCallback } from 'react';
import { DEFAULT_LW, LC, lwAnnual } from '@/lib/data';
import { firstSection, isSection, navFor } from '@/lib/nav';
import { TooltipProvider } from './Tooltip';
import { DrillProvider } from './Drill';
import { FilterProvider } from './FilterContext';
import Sidebar from './Sidebar';
import Home from './views/Home';
import Overview from './views/Overview';
import Structure from './views/Q1';
import WageQuality from './views/Q2';
import Demand from './views/Q3';
import Pathways from './views/Q4';
import Opportunity from './views/Q5';
import Alignment from './views/Q6';
import Regions from './views/Q7';
import About from './views/About';
import Methods from './views/Methods';

// Keyed by the view ids in lib/nav.js, which is where the navigation itself lives.
const COMPONENTS = {
  home: Home,
  overview: Overview,
  regions: Regions,
  structure: Structure,
  wage: WageQuality,
  demand: Demand,
  pathways: Pathways,
  opportunity: Opportunity,
  alignment: Alignment,
  about: About,
  methods: Methods,
};

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
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch (e) {
    /* non-fatal */
  }
}

export default function Dashboard() {
  const [view, setView] = useState('home');
  const [section, setSection] = useState(null);
  const [lw, setLw] = useState(DEFAULT_LW);
  const [collapsed, setCollapsed] = useState(false);

  // Restore after mount so the server and first client render agree.
  useEffect(() => {
    const v = readStored('vt-view', 'home', (x) => !!COMPONENTS[x]);
    setView(v);
    setSection(readStored('vt-sec', firstSection(v), (x) => isSection(v, x)));
    setLw(readStored('vt-lw', DEFAULT_LW, (x) => Object.keys(LC.livingWage).includes(x)));
    setCollapsed(readStored('vt-nav', '', (x) => x === 'collapsed') === 'collapsed');
  }, []);

  const go = useCallback((nextView, nextSection) => {
    const sec = nextSection || firstSection(nextView);
    setView(nextView);
    setSection(sec);
    writeStored('vt-view', nextView);
    writeStored('vt-sec', sec);
    if (typeof window !== 'undefined') window.scrollTo(0, 0);
  }, []);

  const selectLw = useCallback((v) => {
    setLw(v);
    writeStored('vt-lw', v);
  }, []);

  const toggleNav = useCallback(() => {
    setCollapsed((c) => {
      writeStored('vt-nav', c ? '' : 'collapsed');
      return !c;
    });
  }, []);

  const View = COMPONENTS[view] || Home;
  const meta = navFor(view);
  const here = meta && meta.items ? meta.items.filter((x) => x.id === section)[0] : null;

  return (
    <TooltipProvider>
      <DrillProvider>
        <FilterProvider lwAnnual={lwAnnual(lw)}>
          <div className={collapsed ? 'shell navclosed' : 'shell'}>
            <Sidebar
              view={view}
              section={section}
              onGo={go}
              collapsed={collapsed}
              onToggle={toggleNav}
            />

            <main className="main">
              <header className="top">
                <div className="eyebrow">Strada Education Foundation</div>
                {meta && meta.kind === 'group' ? (
                  <p className="crumb">
                    {meta.label}
                    {here ? <span> · {here.label}</span> : null}
                  </p>
                ) : null}
              </header>

              <div className="wrap">
                <section
                  className="view"
                  id={`view-${view}`}
                  aria-label={meta ? meta.label : 'Home'}
                >
                  {view === 'home' ? (
                    <Home onGo={go} />
                  ) : (
                    <View lw={lw} setLw={selectLw} section={section} />
                  )}
                </section>
              </div>
            </main>
          </div>
        </FilterProvider>
      </DrillProvider>
    </TooltipProvider>
  );
}
