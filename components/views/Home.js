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

  // The export's statewide total runs above what the charted occupations sum to:
  // military work and SOCs outside the 22 groups are dropped from every chart. The
  // tile prints the larger figure, so the smaller one belongs in its source card.
  const charted = LC.allOcc.reduce((a, o) => a + (o.j || 0), 0);
  const FOOT = 'Methods lists every source, chart by chart';

  // Four figures, four sources, two universes -- jobs and people, which do not add
  // together. Each tile says which it is on hover.
  const tiles = [
    [
      'Jobs, 2025',
      fmt(TOTJ),
      fmt(LC.allOcc.length) + ' occupations',
      {
        counts:
          'Jobs in Vermont, not people. The charts drop military and unmapped work, so they total less.',
        rows: [
          ['Source', 'Vermont occupation data'],
          ['Vintage', '2025'],
          ['Charted in detail', fmt(charted)],
          ['File', 'lightcast.json'],
          ['Workfile', '01_occupations_master.csv'],
        ],
        foot: FOOT,
      },
    ],
    [
      'Employed Vermonters',
      fmt(GLANCE.emp),
      GLANCE.year + ', monthly average',
      {
        counts: 'People with a job, counted where they live. A survey estimate, not a count.',
        rows: [
          ['Source', 'Census household survey'],
          ['Vintage', GLANCE.year + ', ' + GLANCE.months + ' months'],
          ['Sample', fmt(GLANCE.nPeopleLf) + ' people'],
          ['File', 'glance.json'],
          ['Workfile', '15_labor_force_cps.csv'],
        ],
        foot: FOOT,
      },
    ],
    [
      'Annual openings',
      fmt(LC.openTotal / LC.openYears),
      LC.window,
      {
        counts:
          'Openings a year, including replacing people who leave \u2014 not only new jobs.',
        rows: [
          ['Source', 'Vermont occupation data'],
          ['Vintage', LC.window],
          ['Arithmetic', fmt(LC.openTotal) + ' \u00f7 ' + LC.openYears],
          ['File', 'lightcast.json'],
          ['Workfile', '00_headline_figures.csv'],
        ],
        foot: FOOT,
      },
    ],
    [
      'VSCS completions',
      fmt(SOW.vscs.totalCompletions),
      '2024, ' + SOW.vscs.nCip + ' programs',
      {
        counts: 'Credentials awarded, not people. One graduate finishing two counts twice.',
        rows: [
          ['Source', 'Federal completions data'],
          ['Vintage', '2024 academic year'],
          ['Institutions', 'CCV and Vermont State University'],
          ['File', 'sow.json'],
          ['Workfile', '10_vscs_production.csv'],
        ],
        foot: FOOT,
      },
    ],
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
          <p>Sources, what each measure means, and the rules applied to the data.</p>
          <button type="button" className="browse" onClick={() => onGo('methods', null)}>
            Browse <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
      </div>
    </>
  );
}
