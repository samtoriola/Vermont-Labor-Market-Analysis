/**
 * Short display names for chart axes.
 *
 * The data carries the full SOC and NAICS titles, and those are what tooltips,
 * drill-downs and exports show. In a chart the label gutter is fixed, so the
 * longest of them were being cut mid-word -- "Installation, Maintenance & Repa…"
 * -- which reads as a defect rather than an abbreviation.
 *
 * Two things happen here. A handful of names have an editorial short form, and
 * everything else goes through rules that drop the qualifying clauses BLS titles
 * carry. `trunc` still runs afterwards as the backstop, so a name nobody has
 * shortened is cut rather than overrunning the gutter.
 */

/* Named explicitly, because no rule shortens these without reading oddly. The
   occupational families are all here: they are the axis of several charts, so
   every one of them has to fit. */
const SHORT = {
  // Occupational families (SOC major groups)
  'Healthcare Practitioners & Technical': 'Healthcare Practitioners',
  'Arts, Design, Entertainment & Media': 'Arts, Design & Media',
  'Installation, Maintenance & Repair': 'Installation & Repair',
  'Educational Instruction & Library': 'Education & Library',
  'Transportation & Material Moving': 'Transportation & Moving',
  'Business & Financial Operations': 'Business & Financial',
  'Life, Physical & Social Science': 'Life & Physical Science',
  'Office & Administrative Support': 'Office & Admin Support',

  // Industry sectors (NAICS)
  'Agriculture, Forestry, Fishing & Hunting': 'Agriculture & Forestry',

  // Occupations long enough to be cut even after the clauses come off
  'Secretaries and Administrative Assistants, Except Legal, Medical, and Executive':
    'Secretaries & Admin Assistants',
  'Laborers and Freight, Stock, and Material Movers, Hand': 'Laborers & Material Movers',
  'Market Research Analysts and Marketing Specialists': 'Market Research Analysts',
  'Bookkeeping, Accounting, and Auditing Clerks': 'Bookkeeping & Accounting Clerks',
  'Community and Social Service Specialists, All Other':
    'Community & Social Service Specialists',
};

/**
 * Strips the qualifying tail off a BLS title. These clauses exist to make a
 * title unambiguous within the full classification, which an axis label does not
 * have to do -- "Janitors and Cleaners, Except Maids and Housekeeping Cleaners"
 * is read off a chart as "Janitors and Cleaners".
 */
function stripClauses(s) {
  return s
    .replace(/,\s*(Except|Excluding)\b.*$/i, '')
    .replace(/,\s*All Other$/i, '')
    .trim();
}

/** The name to draw on a chart. Anything already short passes through untouched. */
export function shortLabel(s) {
  const str = String(s);
  if (SHORT[str]) return SHORT[str];
  const stripped = stripClauses(str);
  return SHORT[stripped] || stripped;
}
