/**
 * The whole navigation in one place: what the sidebar lists, what the home page
 * offers, and which section each view opens on.
 *
 * Grouped by what a figure counts, not by where the data came from. The About
 * tab states the rule -- the occupation data counts jobs, the household survey
 * counts people, and the two are not interchangeable -- but the grouping used to
 * break it: a people panel sat under Wage quality beside three jobs panels, and
 * another under Pathways beside two more. A reader moving between neighbouring
 * sections changed unit with nothing saying so. The people panels are their own
 * group now, which is the whole reason Workers exists.
 *
 * Section ids and labels here must match the ones the views declare. They are checked
 * against the views by scripts/verify_app.py, because a label that drifts shows a
 * sidebar entry that opens the wrong panel and nothing else would catch it.
 *
 * `kind: 'item'` is a view with nothing beneath it; `kind: 'group'` is a view whose
 * sections become the entries under its heading.
 */
export const NAV = [
  { kind: 'item', view: 'home', label: 'Home' },
  { kind: 'item', view: 'overview', label: 'Overview' },

  {
    kind: 'group',
    view: 'structure',
    label: 'Employment',
    blurb: 'Which industries and occupational families employ Vermonters, and what each pays.',
    items: [
      { id: 'sectors', label: 'Industry sectors' },
      // Jobs, pay and entry credential were three sections over the same 22 rows.
      // They are one panel now, with the measure on a control.
      { id: 'by-type-of-work', label: 'By type of work' },
    ],
  },
  {
    kind: 'group',
    view: 'wage',
    label: 'Wage quality',
    blurb: 'How the pay of a job compares with a self-sufficiency benchmark, by how big the occupation is.',
    items: [
      // Three measures of one relationship. "Size against pay" was a section of
      // its own and is the same question with the banding taken off, so it is
      // the third measure here rather than a fourth page.
      { id: 'size-and-pay', label: 'Size and pay' },
      // Were two sections over the same 25 rows; one panel, measure on a control.
      { id: 'largest-occupations', label: 'Largest occupations' },
    ],
  },
  {
    kind: 'group',
    view: 'demand',
    label: 'Demand & growth',
    blurb: 'Where openings, advertised demand and projected growth concentrate.',
    items: [
      // Hidden for now: three shares of three different denominators side by side
      // asked more of a reader than it paid back. The section is still in Q3.js.
      // { id: 'three-demand-measures', label: 'Three demand measures' },
      // What employers ask for at the door, from postings: the one panel that
      // compares places rather than ranking categories.
      { id: 'general-demand', label: 'General demand' },
      { id: 'hiring-and-growth', label: 'Hiring and growth' },
      // Hidden for now -- defined in Methods, under "What the measures mean".
      // { id: 'how-openings-are-defined', label: 'How openings are defined' },
    ],
  },
  {
    kind: 'group',
    view: 'pathways',
    label: 'Pathways',
    blurb: 'What each rung of the credential ladder pays, and which credentials open a door. Jobs, not people.',
    items: [
      { id: 'by-credential-level', label: 'By credential level' },
      { id: 'which-credentials-pay', label: 'Which credentials pay' },
      // Hidden for now -- the same contrast is the Overview panel.
      // { id: 'what-this-measures', label: 'What this measures' },
    ],
  },
  {
    kind: 'group',
    view: 'workers',
    label: 'Workers',
    blurb: 'What Vermonters themselves earn, and what the credential a worker holds leads to. People, not jobs.',
    items: [
      { id: 'what-people-hold', label: 'What people hold' },
      { id: 'what-people-earn', label: 'What people earn' },
    ],
  },
  {
    kind: 'group',
    view: 'opportunity',
    label: 'Opportunities',
    blurb: 'Occupations scoring highest on scale, growth, demand and pay — and which VSCS could act on.',
    items: [
      // "By credential" held the same composite scores in a table. The score is
      // computed across every occupation either way, so choosing a credential is
      // a filter on this panel, not a second measure.
      { id: 'highest-scoring', label: 'Highest scoring' },
      { id: 'program-candidates', label: 'Program candidates' },
      // Hidden for now -- a prose restatement of the Program candidates table.
      // { id: 'read-out', label: 'Read out' },
      // Hidden for now -- the same table now sits under the charts it belongs to.
      // { id: 'all-occupations', label: 'All occupations' },
      // Hidden for now -- defined in Methods, under "What the measures mean".
      // { id: 'how-the-index-is-built', label: 'How the index is built' },
    ],
  },
  {
    kind: 'group',
    view: 'alignment',
    label: 'VSCS alignment',
    blurb: 'VSCS credential production set against Vermont occupational demand.',
    items: [
      { id: 'production-by-award', label: 'Production by award' },
      // One question at two grains -- kinds of work, or occupations -- which
      // were two sections. Grain is on a control.
      { id: 'against-demand', label: 'Against demand' },
      // Hidden for now -- defined in Methods, under "What the measures mean".
      // { id: 'how-completions-were-linked', label: 'How completions were linked' },
    ],
  },
  {
    kind: 'group',
    view: 'regions',
    label: 'Regions',
    blurb: 'How jobs, pay, attainment and the local cost floor differ across the 14 counties.',
    items: [
      { id: 'map', label: 'County map' },
      // "All 14 counties" was the same rows and the same columns as the table
      // already folded under the map, so the map's table carries them now --
      // with the county employment and pay figures added to it.
      { id: 'counties', label: 'Counties compared' },
      // Hidden for now -- moved into the "Not covered" list on Methods.
      // { id: 'limits', label: 'What this cannot show' },
    ],
  },

  { kind: 'item', view: 'about', label: 'About' },
  { kind: 'item', view: 'methods', label: 'Methods' },
];

/** Every view id the nav can reach. */
export const VIEW_IDS = NAV.map((n) => n.view);

export function navFor(view) {
  return NAV.filter((n) => n.view === view)[0] || null;
}

/** The section a view opens on when it is reached without one. */
export function firstSection(view) {
  const n = navFor(view);
  return n && n.items && n.items.length ? n.items[0].id : null;
}

export function isSection(view, id) {
  const n = navFor(view);
  return !!(n && n.items && n.items.some((x) => x.id === id));
}
