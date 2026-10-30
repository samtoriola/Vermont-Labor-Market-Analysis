/* Vermont's total employment, the denominator for a family's share. */
import { TOTJ as TOTAL_JOBS } from '@/lib/data';

/**
 * Column specs for the table that sits under each chart.
 *
 * A chart answers one question; the table under it carries everything behind the
 * chart, so a reader can sort it another way, search it, or take the CSV and do
 * their own work with it. `get` returns the underlying value and DataTable renders
 * and sorts from that, which is why sorting by pay orders numerically rather than
 * by the look of "$103,584".
 *
 * Occupation-level panels use occCols() instead — the same spec the full table and
 * the drill-downs use, so an occupation reads the same wherever it appears.
 */

/**
 * The 22 kinds of work. Pass the living-wage figure to get the ratio column; tabs
 * with no benchmark selector leave it out rather than quoting a benchmark the
 * reader never chose.
 */
export function familyCols(lwAnnual) {
  return [
    { k: 'f', label: 'Type of work', kind: 'text', get: (r) => r.f },
    { k: 'jobs', label: 'Jobs today', kind: 'num', get: (r) => r.jobs },
    // The chart draws the share, so the table carries it too; a reader comparing
    // the two should not have to work out which number the bar was.
    { k: 'share', label: 'Share of all jobs', kind: 'rate', get: (r) => (r.jobs / TOTAL_JOBS) * 100 },
    { k: 'jobs21', label: 'Jobs in 2021', kind: 'num', get: (r) => r.jobs21 },
    { k: 'chgPct', label: 'Change since 2021', kind: 'pct', get: (r) => r.chgPct },
    { k: 'g5pct', label: 'Projected by 2030', kind: 'pct', get: (r) => r.g5pct },
    { k: 'med', label: 'Typical pay', kind: 'money', get: (r) => r.med },
    ...(lwAnnual
      ? [
          {
            k: 'lw',
            label: 'Times the living wage',
            kind: 'x',
            get: (r) => (r.med ? r.med / lwAnnual : null),
          },
        ]
      : []),
    { k: 'open', label: 'Openings a year', kind: 'num', get: (r) => r.open },
    { k: 'post', label: 'Job ads, 5 yr', kind: 'num', get: (r) => r.post },
    { k: 'turn', label: 'Turnover', kind: 'rate', get: (r) => r.turn },
    { k: 'lq', label: 'Concentration vs US', kind: 'x', get: (r) => r.lq },
    ...ageCols(),
    { k: 'nocc', label: 'Occupations', kind: 'num', get: (r) => r.nocc },
  ];
}

/**
 * The three age shares, which both the family and the sector tables carry.
 *
 * Shares rather than counts: the question the chart asks is what the mix is, and a
 * count of 55-year-olds in Retail only means something against the size of Retail.
 */
function ageCols() {
  const share = (k) => (r) => {
    const a = r.age;
    if (!a) return null;
    const tot = a.u35 + a.m + a.o55;
    return tot ? (a[k] / tot) * 100 : null;
  };
  return [
    { k: 'u35', label: 'Under 35', kind: 'rate', get: share('u35') },
    { k: 'a35', label: '35 to 54', kind: 'rate', get: share('m') },
    { k: 'o55', label: '55 and over', kind: 'rate', get: share('o55') },
  ];
}

/**
 * The General demand table: one row per place, one column per level.
 *
 * Carries the counts as well as the shares, because the chart can only show
 * composition -- a column holding 651 postings and one holding 70 million are
 * the same height there, and the difference belongs somewhere a reader can find
 * it. `perJob` is the check on reading posting volume as demand.
 */
export function demandCols(order, field, statedField) {
  return [
    { k: 'label', label: 'Place', kind: 'text', get: (r) => r.label },
    { k: 'postings', label: 'Postings', kind: 'num', get: (r) => r.postings },
    { k: statedField, label: 'Stating a level', kind: 'num', get: (r) => r[statedField] },
    {
      k: 'statedPct',
      label: 'Share stating one',
      kind: 'rate',
      get: (r) => (r.postings ? (r[statedField] / r.postings) * 100 : null),
    },
    { k: 'perJob', label: 'Postings per job', kind: 'num2', get: (r) => r.perJob },
    ...order.map((name, i) => ({
      k: `${field}${i}`,
      label: name,
      kind: 'rate',
      get: (r) => (r[statedField] ? (r[field][i] / r[statedField]) * 100 : null),
    })),
  ];
}

/** Industry sectors. The industry export carries no 2021 column, so no change here. */
export function sectorCols() {
  return [
    { k: 's', label: 'Industry', kind: 'text', get: (r) => r.s },
    { k: 'j', label: 'Jobs', kind: 'num', get: (r) => r.j },
    { k: 'share', label: 'Share of all jobs', kind: 'pct', get: (r) => r.share },
    { k: 'earn', label: 'Average pay per job', kind: 'money', get: (r) => r.earn },
    ...ageCols(),
    { k: 'nnaics', label: 'Industries in sector', kind: 'num', get: (r) => r.nnaics },
  ];
}

/** The detailed industries inside a sector. */
export function industryCols() {
  return [
    { k: 'n', label: 'Industry', kind: 'text', get: (r) => r.n },
    { k: 'naics', label: 'Industry code', kind: 'text', get: (r) => r.naics },
    { k: 'j', label: 'Jobs', kind: 'num', get: (r) => r.j },
    { k: 'earn', label: 'Average pay per job', kind: 'money', get: (r) => r.earn },
  ];
}

/**
 * Size bands and credential tiers, which carry the same measures under different
 * names: size bands key off `s`, tiers off `t`.
 */
export function bandCols(lwAnnual, key = 's', label = 'Group') {
  return [
    { k: key, label, kind: 'text', get: (r) => r[key] },
    { k: 'jobs', label: 'Jobs today', kind: 'num', get: (r) => r.jobs },
    { k: 'share', label: 'Share of all jobs', kind: 'pct', get: (r) => r.share },
    { k: 'med', label: 'Typical pay', kind: 'money', get: (r) => r.med },
    {
      k: 'lw',
      label: 'Times the living wage',
      kind: 'x',
      get: (r) => (r.med ? r.med / lwAnnual : null),
    },
    { k: 'open', label: 'Openings a year', kind: 'num', get: (r) => r.open },
    { k: 'chgPct', label: 'Change since 2021', kind: 'pct', get: (r) => r.chgPct },
    { k: 'g5pct', label: 'Projected by 2030', kind: 'pct', get: (r) => r.g5pct },
    { k: 'nocc', label: 'Occupations', kind: 'num', get: (r) => r.nocc },
  ];
}

/**
 * The 14 counties, both sides at once: the jobs in the county and the people
 * living in it.
 *
 * These come from different places and count different things -- `emp` and
 * `med` are jobs located in the county, `pop`, `ba` and `inc` are the residents,
 * who may work in another one. They are in one table because a reader comparing
 * them is going to put them side by side anyway, and doing it here is the only
 * version where the column headings say which is which.
 */
export function countyCols() {
  return [
    { k: 'c', label: 'County', kind: 'text', get: (r) => r.c },
    { k: 'emp', label: 'Jobs in the county', kind: 'num', get: (r) => r.emp },
    { k: 'med', label: 'Typical job pays', kind: 'money', get: (r) => r.med },
    { k: 'chg', label: 'Change in jobs since 2021', kind: 'pct', get: (r) => r.chg },
    { k: 'pop', label: 'Population', kind: 'num', get: (r) => r.pop },
    { k: 'ba', label: 'Adults with a degree', kind: 'rate', get: (r) => r.ba },
    { k: 'inc', label: 'Typical household income', kind: 'money', get: (r) => r.inc },
    { k: 'lwH', label: 'Living wage an hour', kind: 'money', get: (r) => r.lwH },
    { k: 'lwA', label: 'Living wage a year', kind: 'money', get: (r) => r.lwA },
    { k: 'incLw', label: 'Times the living wage', kind: 'x', get: (r) => r.incLw },
  ];
}

/** Every county-and-family pair behind the concentration grid. */
export function countyMixCols() {
  return [
    { k: 'c', label: 'County', kind: 'text', get: (r) => r.c },
    { k: 'f', label: 'Type of work', kind: 'text', get: (r) => r.f },
    { k: 'jobs', label: 'Jobs', kind: 'num', get: (r) => r.jobs },
    { k: 'mix', label: 'Share of the county', kind: 'rate', get: (r) => r.mix },
    { k: 'st', label: 'Share of Vermont', kind: 'rate', get: (r) => r.st },
    { k: 'lq', label: 'Times the state share', kind: 'x', get: (r) => r.lq },
  ];
}

/**
 * Scored occupations. The four component scores are carried alongside the total,
 * because a score is only arguable if you can see what it is made of.
 */
export function scoreCols() {
  return [
    { k: 'n', label: 'Occupation', kind: 'text', get: (r) => r.n },
    { k: 'sc', label: 'Score', kind: 'num1', get: (r) => r.sc },
    { k: 'j', label: 'Jobs', kind: 'num', get: (r) => r.j },
    { k: 'm', label: 'Typical pay', kind: 'money', get: (r) => r.m },
    { k: 'lw', label: 'Times the living wage', kind: 'x', get: (r) => r.lw },
    { k: 'o', label: 'Openings a year', kind: 'num', get: (r) => r.o },
    { k: 'pp', label: 'Ads per 100 jobs', kind: 'num1', get: (r) => r.pp },
    { k: 'g', label: 'Projected by 2030', kind: 'pct', get: (r) => r.g },
    { k: 't', label: 'Entry credential', kind: 'text', get: (r) => r.t },
    { k: 's_size', label: 'Score: employment', kind: 'num1', get: (r) => r.s_size },
    { k: 's_growth', label: 'Score: growth', kind: 'num1', get: (r) => r.s_growth },
    { k: 's_postings', label: 'Score: job ads', kind: 'num1', get: (r) => r.s_postings },
    { k: 's_pay', label: 'Score: pay', kind: 'num1', get: (r) => r.s_pay },
  ];
}

/**
 * Survey groups from the person-level charts -- the three places, and the six
 * credentials people hold.
 *
 * The rows here are groups, not the individual dots: a dot is one anonymous
 * respondent, and the useful export is the shape of each group rather than a
 * sample of the microdata. The percentiles are what the chart's lines are drawn
 * from, so the table and the chart cannot disagree.
 */
export function peopleCols(label = 'Group') {
  return [
    { k: 'label', label, kind: 'text', get: (r) => r.label },
    { k: 'n', label: 'Respondents', kind: 'num', get: (r) => r.n },
    { k: 'pop', label: 'Workers represented', kind: 'num', get: (r) => r.pop },
    { k: 'med', label: 'Midpoint earnings', kind: 'money', get: (r) => r.med },
    { k: 'avg', label: 'Average earnings', kind: 'money', get: (r) => r.avg },
    { k: 'p10', label: 'Lowest-paid tenth', kind: 'money', get: (r) => r.p10 },
    { k: 'p25', label: 'Lower quarter', kind: 'money', get: (r) => r.p25 },
    { k: 'p75', label: 'Upper quarter', kind: 'money', get: (r) => r.p75 },
    { k: 'p90', label: 'Highest-paid tenth', kind: 'money', get: (r) => r.p90 },
  ];
}

/** The percentile ladder rows: one occupation, its spread, midpoint and average. */
export function ladderCols(lwAnnual) {
  return [
    { k: 'label', label: 'Occupation', kind: 'text', get: (r) => r.label },
    { k: 'med', label: 'Midpoint pay', kind: 'money', get: (r) => r.med },
    { k: 'mu', label: 'Average pay', kind: 'money', get: (r) => r.mu },
    { k: 'p10', label: 'Lowest-paid tenth', kind: 'money', get: (r) => r.p10 },
    { k: 'p25', label: 'Lower quarter', kind: 'money', get: (r) => r.p25 },
    { k: 'p75', label: 'Upper quarter', kind: 'money', get: (r) => r.p75 },
    { k: 'p90', label: 'Highest-paid tenth', kind: 'money', get: (r) => r.p90 },
    ...(lwAnnual
      ? [
          {
            k: 'lw',
            label: 'Times the living wage',
            kind: 'x',
            get: (r) => (r.med ? r.med / lwAnnual : null),
          },
        ]
      : []),
  ];
}

/** VSCS awards. */
export function awardCols(total) {
  return [
    { k: 'a', label: 'Award', kind: 'text', get: (r) => r.a },
    { k: 'c', label: 'Graduates', kind: 'num', get: (r) => r.c },
    {
      k: 'share',
      label: 'Share of all awards',
      kind: 'rate',
      get: (r) => (total ? (r.c / total) * 100 : null),
    },
  ];
}
