'use client';

import { NAV } from '@/lib/nav';
import { LC, TOTJ, DATA, SOW, GLANCE } from '@/lib/data';
import { fmt } from '@/lib/format';
import { Tiles } from '../ui';

/**
 * The landing page: what this is, the headline figures, and a card per topic. The
 * cards repeat the sidebar on purpose -- someone arriving cold needs to know what each
 * topic contains before picking one, which a list of labels does not tell them.
 */
export default function Home({ onGo }) {
  const groups = NAV.filter((n) => n.kind === 'group');

  const tiles = [
    ['Jobs, 2025', fmt(TOTJ), 'Lightcast, ' + fmt(LC.allOcc.length) + ' occupations'],
    ['Employed Vermonters', fmt(GLANCE.emp), 'CPS ' + GLANCE.year + ', monthly average'],
    ['Annual openings', fmt(LC.openTotal / LC.openYears), 'Lightcast, ' + LC.window],
    ['VSCS completions', fmt(SOW.vscs.totalCompletions), 'IPEDS 2024, ' + SOW.vscs.nCip + ' programs'],
  ];

  return (
    <>
      <div className="homehead">
        <h2>Vermont Labor Market Overview</h2>
        <p>
          A guided look at Vermont&rsquo;s labor market and how VSCS credential production
          sits against it. Pick a topic to jump in; the sidebar lists every question within
          that topic.
        </p>
      </div>

      <Tiles items={tiles} />

      <div className="homecards">
        {groups.map((g) => (
          <div className="homecard" key={g.view}>
            <h3>{g.label}</h3>
            <p>{g.blurb}</p>
            <button type="button" className="browse" onClick={() => onGo(g.view, g.items[0].id)}>
              Browse <span aria-hidden="true">&rarr;</span>
            </button>
          </div>
        ))}
      </div>

      <div className="homecards">
        <div className="homecard quiet">
          <h3>About</h3>
          <p>What this covers, where the numbers come from, and how to drive it.</p>
          <button type="button" className="browse" onClick={() => onGo('about', null)}>
            Browse <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
        <div className="homecard quiet">
          <h3>Methods</h3>
          <p>Sources, what each measure means, the rules applied, and what is not covered.</p>
          <button type="button" className="browse" onClick={() => onGo('methods', null)}>
            Browse <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
      </div>
    </>
  );
}
