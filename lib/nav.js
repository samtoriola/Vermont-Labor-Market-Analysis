/**
 * The whole navigation in one place: what the sidebar lists, what the home page
 * offers, and which section each view opens on.
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
    view: 'regions',
    label: 'Regions',
    blurb: 'How attainment, earnings and the local cost floor differ across the 14 counties.',
    items: [
      { id: 'map', label: 'County map' },
      { id: 'all-counties', label: 'All 14 counties' },
      { id: 'limits', label: 'What this cannot show' },
    ],
  },
  {
    kind: 'group',
    view: 'structure',
    label: 'Employment',
    blurb: 'Which industries and occupational families employ Vermonters, and what each pays.',
    items: [
      { id: 'sectors', label: 'Industry sectors' },
      { id: 'jobs', label: 'Jobs by family' },
      { id: 'pay', label: 'Median pay' },
      { id: 'credential', label: 'Entry credential' },
    ],
  },
  {
    kind: 'group',
    view: 'wage',
    label: 'Wage quality',
    blurb: 'How pay compares with a self-sufficiency benchmark, by occupation and by worker.',
    items: [
      { id: 'wage-quality-by-size', label: 'Wage quality by size' },
      { id: 'median-pay-by-size', label: 'Median pay by size' },
      { id: 'worker-earnings', label: 'Worker earnings' },
      { id: '25-largest-by-jobs', label: '25 largest by jobs' },
      { id: 'mean-against-median', label: 'Mean against median' },
      { id: 'size-against-pay', label: 'Size against pay' },
    ],
  },
  {
    kind: 'group',
    view: 'demand',
    label: 'Demand & growth',
    blurb: 'Where openings, advertised demand and projected growth concentrate.',
    items: [
      { id: 'three-demand-measures', label: 'Three demand measures' },
      { id: 'postings-index', label: 'Postings index' },
      { id: 'observed-change', label: 'Observed change' },
      { id: 'projected-growth', label: 'Projected growth' },
      { id: 'how-openings-are-defined', label: 'How openings are defined' },
    ],
  },
  {
    kind: 'group',
    view: 'pathways',
    label: 'Pathways',
    blurb: 'What each rung of the credential ladder pays, and which credentials open a door.',
    items: [
      { id: 'employment-and-dispersion', label: 'Employment and dispersion' },
      { id: 'what-the-job-requires', label: 'What the job requires' },
      { id: 'what-people-hold', label: 'What people hold' },
      { id: 'above-the-living-wage', label: 'Above the living wage' },
      { id: 'which-credentials-pay', label: 'Which credentials pay' },
      { id: 'what-this-measures', label: 'What this measures' },
    ],
  },
  {
    kind: 'group',
    view: 'opportunity',
    label: 'Opportunities',
    blurb: 'Occupations scoring highest on scale, growth, demand and pay — and which VSCS could act on.',
    items: [
      { id: 'highest-scoring', label: 'Highest scoring' },
      { id: 'by-credential-tier', label: 'By credential tier' },
      { id: 'program-candidates', label: 'Program candidates' },
      { id: 'read-out', label: 'Read out' },
      { id: 'all-occupations', label: 'All occupations' },
      { id: 'how-the-index-is-built', label: 'How the index is built' },
    ],
  },
  {
    kind: 'group',
    view: 'alignment',
    label: 'VSCS alignment',
    blurb: 'VSCS credential production set against Vermont occupational demand.',
    items: [
      { id: 'production-by-award', label: 'Production by award' },
      { id: 'against-openings', label: 'Against openings' },
      { id: 'production-against-demand', label: 'Production vs demand' },
      { id: 'how-completions-were-linked', label: 'How completions were linked' },
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
