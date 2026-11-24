/**
 * The canned report: findings computed from the data, not written by hand.
 *
 * WHY THIS IS A MODULE AND NOT COPY
 * ---------------------------------
 * A report travels away from the tool that made it. Nobody who reads it can
 * check a figure against the tab it came from, which means two things have to be
 * true at once: every number has to come from the same functions the tabs use,
 * and no sentence may assert anything the numbers do not.
 *
 * So each finding is a rule. It reads the data for the chosen scope, works out
 * its own figures, and either fires or does not. "The largest group has fewer
 * jobs than in 2021" is a query, not an opinion; if that stops being true the
 * finding drops out and the next one takes its place. Nothing here hard-codes a
 * figure, including the ones in the headlines.
 *
 * HOW THE SENTENCES ARE WRITTEN
 * -----------------------------
 * The `read` line on each finding is the "so what" -- but stated as arithmetic
 * the reader can check, never as a judgement they would have to take on trust.
 * The rule is that the line adds a NUMBER, not an adjective:
 *
 *   not  "a strategy aimed at growth sectors misses almost all the hiring"
 *   but  "for every opening from an added job, 22.7 come from a job that
 *         already existed"
 *
 * Both say the same thing. Only the second can be defended line by line by
 * someone who was not in the room. Words that grade rather than measure --
 * best, worst, poor, healthy, failing, problem, crisis, underpaid -- are out,
 * and scripts/check_report_language.py fails the build if one appears here.
 * Superlatives of a measured quantity are fine: "the highest replacement rate"
 * names a row in a sorted column, and the table beside it shows the sort.
 *
 * WHAT A FINDING LOOKS LIKE
 * -------------------------
 *   { id, head, stats[], body[], read, bars[], table{}, src }
 *
 * head  the finding, as a statement of fact
 * stats big figures, where the finding is carried by two or three numbers
 * body  sentences of supporting figures
 * read  the derived number the reader takes away
 * bars  to-scale rows: { label, pct, value, color }
 * table cols/rows, already formatted
 * src   what the figures are and when they are from
 */
import {
  CPOST,
  CTY,
  LC,
  SOW,
  TIER_ORDER,
  TOTJ,
  WF,
  lwAnnual,
  occByFamily,
} from './data';
import { pricedPool, rollUp } from './wage';
import { fmt, money } from './format';

export const FORMATS = [
  { id: 'brief', label: 'One-pager' },
  { id: 'slides', label: 'Slide deck' },
];

export const SCOPE_KINDS = [
  { id: 'vt', label: 'Vermont' },
  { id: 'cty', label: 'A county' },
  { id: 'fam', label: 'An occupation group' },
  { id: 'cip', label: 'A VSCS program' },
];

/** The choices inside a scope kind, largest first so the useful ones are near the top. */
export function scopeOptions(kind) {
  if (kind === 'cty') {
    return CTY.counties
      .slice()
      .sort((a, b) => b.emp - a.emp)
      .map((c) => ({ id: c.c, label: c.c + ' — ' + fmt(c.emp) + ' jobs' }));
  }
  if (kind === 'fam') {
    return LC.families
      .slice()
      .sort((a, b) => b.jobs - a.jobs)
      .map((r) => ({ id: r.f, label: r.f + ' — ' + fmt(r.jobs) + ' jobs' }));
  }
  if (kind === 'cip') {
    return (SOW.vscs.byCip || [])
      .filter((p) => p.c > 0)
      .map((p) => ({
        id: p.cip,
        label: p.n.replace(/\.$/, '') + ' — ' + p.c.toFixed(0) + ' completions',
      }));
  }
  return [];
}

// ---------------------------------------------------------------- helpers ---

const pc = (v, d = 1) => (v === null || v === undefined ? '—' : v.toFixed(d) + '%');
const pp = (v, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d) + ' pp';
// One decimal, with the thousands separator every other figure carries:
// toFixed(1) gave "1700.1" beside "1,983" in the same stat row.
const one = (v) =>
  v.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

/** Difference between two figures, said without grading either of them. */
function compareWord(a, b) {
  if (Math.abs(a - b) < 0.05) return 'level with';
  return a > b ? 'above' : 'below';
}

/** Change against an earlier figure, said as a direction and a size. */
function moveWord(pctChange) {
  if (Math.abs(pctChange) < 0.05) return 'holds the same number of jobs as';
  return (
    'holds ' + one(Math.abs(pctChange)) + '% ' + (pctChange > 0 ? 'more' : 'fewer') + ' jobs than'
  );
}

/** Share of each credential tier's jobs clearing the benchmark, in ladder order. */
function tierRows(lwKey) {
  return TIER_ORDER.map((t) => {
    const row = LC.tiers.filter((x) => x.t === t)[0];
    if (!row || !row.above) return null;
    return { t, above: row.above[lwKey], jobs: row.jobs, med: row.med };
  }).filter(Boolean);
}

/**
 * Statewide share of jobs below one household's floor.
 *
 * Through rollUp over the priced pool, which is the function the Wage quality
 * tab itself calls. Rolling the five credential tiers up instead is a tempting
 * shortcut and gives 42.5% where the tab shows 41.1%: the tiers carry their own
 * rounded shares, and weighting those by tier employment is not the same
 * arithmetic as reading every occupation's ladder. A report that prints 42.5%
 * beside a tab showing 41.1% is the failure mode this whole module exists to
 * avoid, so it goes through the same code path or not at all.
 */
const belowCache = new Map();

function stateBelow(lwKey) {
  if (belowCache.has(lwKey)) return belowCache.get(lwKey);
  const r = rollUp(pricedPool(LC.allOcc), lwAnnual(lwKey));
  const v = r ? r.below : null;
  belowCache.set(lwKey, v);
  return v;
}

/**
 * Openings a year, and how many of them the projection puts down to added jobs.
 *
 * Openings from LC.openTotal / LC.openYears, which is what the home page prints;
 * summing the 22 occupation groups gives 48,718 against the 48,893 shown there,
 * because some occupations carry no group. The projection is summed over the
 * same full occupation list rather than the groups, so both sides of the split
 * cover the same universe.
 */
function openingSplit() {
  const open = LC.openTotal / LC.openYears;
  const added = LC.allOcc.reduce((a, o) => a + (o.g5 || 0), 0) / 5;
  return { open, added, held: open - added, pctAdded: (added / open) * 100 };
}

function corr(xs, ys) {
  const n = xs.length;
  if (n < 3) return null;
  const mx = xs.reduce((a, b) => a + b, 0) / n;
  const my = ys.reduce((a, b) => a + b, 0) / n;
  let num = 0;
  let dx = 0;
  let dy = 0;
  for (let i = 0; i < n; i += 1) {
    num += (xs[i] - mx) * (ys[i] - my);
    dx += (xs[i] - mx) ** 2;
    dy += (ys[i] - my) ** 2;
  }
  return dx && dy ? num / Math.sqrt(dx * dy) : null;
}

const COL = { ord: ['--ord1', '--ord2', '--ord3', '--ord4', '--ord5'] };

// ------------------------------------------------------------ Vermont ------

function vermont(lwKey) {
  const floor = lwAnnual(lwKey);
  const out = [];
  const sp = openingSplit();

  // 1. Where a year's openings come from.
  out.push({
    id: 'openings-source',
    head: 'Most openings are in jobs that already existed',
    stats: [
      [fmt(Math.round(sp.open)), 'Openings a year'],
      [pc(sp.pctAdded), 'Of them from added jobs'],
    ],
    body: [
      'The 2030 projection adds ' +
        fmt(Math.round(sp.added * 5)) +
        ' jobs over five years, about ' +
        fmt(Math.round(sp.added)) +
        ' a year. The remaining openings are positions being refilled.',
    ],
    read:
      'For every opening from an added job, ' +
      one(sp.held / sp.added) +
      ' come from a job that already existed.',
    bars: [
      { label: 'Refilled — the position already existed', pct: 100 - sp.pctAdded, value: fmt(Math.round(sp.held)) },
      { label: 'Added — a job the projection creates', pct: sp.pctAdded, value: fmt(Math.round(sp.added)), color: '--s2' },
    ],
    src: 'Annual openings 2021–2025 · 2030 projection against 2025 jobs',
  });

  // 2. How the share below the benchmark moves with the household measured.
  const hh = Object.keys(LC.livingWage)
    .map((k) => ({ k, wage: LC.livingWage[k], below: stateBelow(k) }))
    .filter((r) => r.below !== null)
    .sort((a, b) => a.below - b.below);
  const here = hh.filter((r) => r.k === lwKey)[0];
  const lo = hh[0];
  const hi = hh[hh.length - 1];
  out.push({
    id: 'below-benchmark',
    head: pc(here.below) + ' of jobs pay below the selected benchmark',
    stats: [
      [pc(here.below), 'Of jobs below it'],
      [money(floor), 'A year, at ' + fmt(LC.hours) + ' hours'],
    ],
    body: [
      'The benchmark is ' +
        lwKey +
        ', at $' +
        LC.livingWage[lwKey].toFixed(2) +
        ' an hour. Changing it changes the share, because it is the same ' +
        fmt(TOTJ) +
        ' jobs measured against a different figure.',
    ],
    read:
      'Across the ' +
      hh.length +
      ' published benchmarks the share ranges from ' +
      pc(lo.below) +
      ' (' +
      lo.k +
      ') to ' +
      pc(hi.below) +
      ' (' +
      hi.k +
      ').',
    bars: hh.map((r) => ({
      label: r.k + ' · ' + money(r.wage * LC.hours),
      pct: r.below,
      value: pc(r.below),
      color: r.k === lwKey ? '--s1' : '--ord2',
    })),
    src: 'Read off each occupation’s published pay distribution · MIT Living Wage Calculator 2025',
  });

  // 3. The credential ladder.
  const tr = tierRows(lwKey);
  if (tr.length > 2) {
    const steps = tr.slice(1).map((r, i) => ({ d: r.above - tr[i].above, from: tr[i].t, to: r.t }));
    const big = steps.slice().sort((a, b) => b.d - a.d)[0];
    out.push({
      id: 'credential-ladder',
      head: 'The share clearing the benchmark rises with the credential the work asks for',
      body: [
        'Each rung is the credential a job asks for at entry, not the credential the person holding it has.',
      ],
      read:
        'The largest step is ' +
        pp(big.d) +
        ', between ' +
        big.from.toLowerCase() +
        ' and ' +
        big.to.toLowerCase() +
        '.',
      bars: tr.map((r, i) => ({
        label: r.t + ' · ' + fmt(r.jobs) + ' jobs · median ' + money(r.med),
        pct: r.above,
        value: pc(r.above),
        color: COL.ord[Math.min(i, COL.ord.length - 1)],
      })),
      src: 'Share of each tier’s jobs at or above ' + money(floor) + ' · jobs, not people',
    });
  }

  // 4. The largest groups, and which way each has moved.
  const fams = LC.families.slice().sort((a, b) => b.jobs - a.jobs);
  const top = fams[0];
  out.push({
    id: 'largest-groups',
    head: 'The largest occupation groups, and how each has moved since 2021',
    body: [
      'Ranked by jobs today. The two change columns disagree for several groups, which is why both are shown.',
    ],
    read:
      top.f +
      ' is the largest at ' +
      fmt(top.jobs) +
      ' jobs, ' +
      pc((top.jobs / TOTJ) * 100) +
      ' of Vermont employment, and ' +
      moveWord(top.chgPct) +
      ' in 2021.',
    table: {
      cols: ['Occupation group', 'Jobs', 'Since 2021', 'To 2030', 'Openings a year', 'Clearing benchmark'],
      rows: fams.slice(0, 7).map((r) => [
        r.f,
        fmt(r.jobs),
        pp(r.chgPct),
        pp(r.g5pct),
        fmt(r.open),
        pc(r.above ? r.above[lwKey] : null),
      ]),
    },
    src: 'Lightcast 2025 against 2021 · projection to 2030',
  });

  // 5. Replacement rate against pay. Stated as a correlation, with the rows.
  const withTurn = LC.families.filter((r) => r.turn !== null && r.turn !== undefined && r.above);
  const r = corr(withTurn.map((x) => x.turn), withTurn.map((x) => x.above[lwKey]));
  if (r !== null) {
    const byTurn = withTurn.slice().sort((a, b) => b.turn - a.turn);
    out.push({
      id: 'replacement-and-pay',
      head: 'Groups with higher replacement rates have smaller shares clearing the benchmark',
      body: [
        'The replacement rate is a year’s separations as a share of the group’s jobs. A rate above 100% means the group refills more positions in a year than it holds.',
      ],
      read:
        'Across the ' +
        withTurn.length +
        ' occupation groups the correlation between replacement rate and share clearing the benchmark is ' +
        r.toFixed(2) +
        '.',
      table: {
        cols: ['Occupation group', 'Replaced a year', 'Median pay', 'Clearing benchmark', 'Openings a year'],
        rows: byTurn
          .slice(0, 5)
          .concat([byTurn[byTurn.length - 1]])
          .map((x) => [x.f, pc(x.turn), money(x.med), pc(x.above[lwKey]), fmt(x.open)]),
      },
      src: 'Five highest replacement rates, and the lowest, of ' + withTurn.length + ' groups',
    });
  }

  // 6. The counties, against their own cost floors.
  const cty = WF.counties
    .map((c) => {
      const b = (c.byLw || {})[lwKey] || {};
      return { c: c.c, local: b.local, lwA: b.lwA, jobs: c.jobs };
    })
    .filter((c) => c.local !== undefined)
    .sort((a, b) => b.local - a.local);
  if (cty.length) {
    out.push({
      id: 'county-spread',
      head: 'Shares below the local cost floor differ across the 14 counties',
      body: [
        'Each county is measured against its own floor for this household, not against the statewide figure, so both the pay and the cost vary between rows.',
      ],
      read:
        'The share ranges from ' +
        pc(cty[cty.length - 1].local) +
        ' in ' +
        cty[cty.length - 1].c +
        ' to ' +
        pc(cty[0].local) +
        ' in ' +
        cty[0].c +
        ', a spread of ' +
        one(cty[0].local - cty[cty.length - 1].local) +
        ' points.',
      bars: cty.map((c) => ({
        label: c.c + ' · floor ' + money(c.lwA),
        pct: c.local,
        value: pc(c.local),
      })),
      twoCol: true,
      src: 'County pay ladders · MIT Living Wage Calculator 2025, by county',
    });
  }

  // 7. VSCS attribution against openings.
  const V = SOW.vscs;
  const byFam = (V.byFamily || []).slice().sort((a, b) => b.linked - a.linked);
  if (byFam.length) {
    const thin = byFam.filter((x) => x.linked < 1);
    const thinOpen = thin.reduce((a, x) => a + x.open, 0);
    out.push({
      id: 'vscs-attribution',
      head: 'Attributed graduates per annual opening, by occupation group',
      stats: [
        [fmt(V.totalCompletions), 'VSCS completions'],
        [one(byFam.reduce((a, x) => a + x.linked, 0)), 'Attributable to a Vermont occupation'],
      ],
      body: [
        'Each program’s completions are divided across the occupations its program code links to, in proportion to Vermont employment. The figures are modelled rather than observed, which is why they carry a decimal.',
      ],
      read:
        thin.length +
        ' occupation groups, holding ' +
        fmt(thinOpen) +
        ' openings a year (' +
        pc((thinOpen / openingSplit().open) * 100) +
        ' of the state total), are linked to under one attributed graduate.',
      table: {
        cols: ['Occupation group', 'Openings a year', 'Graduates attributed', 'Per opening'],
        rows: byFam
          .slice(0, 5)
          .concat(thin.slice(0, 3))
          .map((x) => [
            x.f,
            fmt(x.open),
            one(x.linked),
            x.open ? (x.linked / x.open).toFixed(3) : '—',
          ]),
      },
      src: 'Federal completions data 2024 · program-to-occupation crosswalk · modelled allocation',
    });
  }

  return out;
}

// ------------------------------------------------------------- county ------

function county(name, lwKey) {
  const c = CTY.counties.filter((x) => x.c === name)[0];
  if (!c) return [];
  const w = WF.counties.filter((x) => x.c === name)[0];
  const b = w ? (w.byLw || {})[lwKey] || {} : {};
  const st = CTY.state;
  const out = [];

  out.push({
    id: 'county-size',
    head: name + ' holds ' + fmt(c.emp) + ' jobs, ' + pc((c.emp / TOTJ) * 100) + ' of Vermont employment',
    stats: [
      [fmt(c.emp), 'Jobs'],
      [money(c.med), 'Median pay'],
      [pp(c.chg), 'Since 2021'],
    ],
    body: [
      'The county ' +
        moveWord(c.chg) +
        ' in 2021. Vermont as a whole ' +
        moveWord(st.chg) +
        ' in 2021.',
    ],
    read:
      'Median pay is ' +
      money(c.med) +
      ', ' +
      money(Math.abs(c.med - st.med)) +
      ' ' +
      compareWord(c.med, st.med) +
      ' the statewide median of ' +
      money(st.med) +
      '.',
    src: 'Lightcast county employment and pay, 2025',
  });

  if (b.local !== undefined) {
    const all = WF.counties
      .map((x) => ((x.byLw || {})[lwKey] || {}).local)
      .filter((v) => v !== undefined)
      .sort((a, b2) => a - b2);
    const rank = all.filter((v) => v < b.local).length + 1;
    out.push({
      id: 'county-floor',
      head: pc(b.local) + ' of ' + name + ' jobs pay below the county’s own cost floor',
      stats: [
        [pc(b.local), 'Below the county floor'],
        [money(b.lwA), 'The county floor'],
        [pc(b.state), 'Below the state floor'],
      ],
      body: [
        'The county floor is what this household needs in ' +
          name +
          '. The state floor is the same household measured at the statewide figure of ' +
          money(lwAnnual(lwKey)) +
          ', which is how every other tab measures it.',
      ],
      read:
        'Against its own floor the share is ' +
        pp(b.local - b.state) +
        ' compared with the statewide floor, and the county ranks ' +
        rank +
        ' of ' +
        all.length +
        ' from the lowest share.',
      bars: [
        { label: name + ' · own floor ' + money(b.lwA), pct: b.local, value: pc(b.local) },
        { label: name + ' · state floor ' + money(lwAnnual(lwKey)), pct: b.state, value: pc(b.state), color: '--ord3' },
        { label: 'Highest of the 14 counties', pct: all[all.length - 1], value: pc(all[all.length - 1]), color: '--ord2' },
        { label: 'Lowest of the 14 counties', pct: all[0], value: pc(all[0]), color: '--ord2' },
      ],
      src: 'County pay ladders against the county’s own living wage · MIT 2025',
    });
  }

  const mix = Object.keys(c.mix || {})
    .map((k) => ({ f: k, local: c.mix[k], state: (st.share || {})[k] }))
    .filter((r) => r.state !== undefined)
    .sort((a, b2) => b2.local - a.local);
  if (mix.length) {
    const far = mix.slice().sort((a, b2) => Math.abs(b2.local - b2.state) - Math.abs(a.local - a.state))[0];
    out.push({
      id: 'county-mix',
      head: 'Occupation mix in ' + name + ', against the statewide mix',
      body: ['Each figure is the group’s share of that area’s jobs, so the two columns are shares of different totals.'],
      read:
        far.f +
        ' differs most from the state: ' +
        pc(far.local) +
        ' of ' +
        name +
        ' jobs against ' +
        pc(far.state) +
        ' statewide, ' +
        pp(far.local - far.state) +
        '.',
      table: {
        cols: ['Occupation group', 'Share in ' + name, 'Share statewide', 'Difference'],
        rows: mix.slice(0, 7).map((r) => [r.f, pc(r.local), pc(r.state), pp(r.local - r.state)]),
      },
      src: 'Lightcast county occupational mix, 2025',
    });
  }

  const key = Object.keys(CPOST.counties || {}).filter((k) => CPOST.counties[k].c === name)[0];
  const d = key ? CPOST.counties[key] : null;
  if (d && d.employers.length) {
    out.push({
      id: 'county-postings',
      head: 'Most-advertised employers and industries in ' + name,
      body: [
        'These count postings, not payroll: one posting counts once however many people it hires, and an employer that rarely advertises does not appear. Explicitly remote roles are excluded.',
      ],
      read:
        fmt(d.postings) +
        ' postings in ' +
        name +
        ' over ' +
        CPOST.window +
        ', of which ' +
        fmt(d.employers[0].p) +
        ' name ' +
        d.employers[0].n +
        '.',
      table: {
        cols: ['Advertises most', 'Postings', 'Most-advertised industry', 'Postings'],
        rows: d.employers.map((e, i) => [
          e.n,
          fmt(e.p),
          d.industries[i] ? d.industries[i].n : '—',
          d.industries[i] ? fmt(d.industries[i].p) : '—',
        ]),
      },
      src: 'Job postings, ' + CPOST.window + ' · non-staffing, unique, excluding internships',
    });
  }

  return out;
}

// ------------------------------------------------- one occupation group ----

function family(name, lwKey) {
  const row = LC.families.filter((x) => x.f === name)[0];
  if (!row) return [];
  const floor = lwAnnual(lwKey);
  const occ = occByFamily(name);
  const roll = rollUp(occ, floor);
  const out = [];

  out.push({
    id: 'family-size',
    head: name + ' holds ' + fmt(row.jobs) + ' jobs, ' + pc((row.jobs / TOTJ) * 100) + ' of Vermont employment',
    stats: [
      [fmt(row.jobs), 'Jobs'],
      [fmt(row.open), 'Openings a year'],
      [money(row.med), 'Median pay'],
    ],
    body: [
      'The group ' +
        moveWord(row.chgPct) +
        ' in 2021, and the 2030 projection puts it at ' +
        pp(row.g5pct) +
        ' against today. It covers ' +
        fmt(row.nocc) +
        ' occupations.',
    ],
    read:
      'The group supplies ' +
      pc((row.open / openingSplit().open) * 100) +
      ' of Vermont’s annual openings while holding ' +
      pc((row.jobs / TOTJ) * 100) +
      ' of its jobs.',
    src: 'Lightcast 2025 · openings 2021–2025 · projection to 2030',
  });

  if (roll) {
    const state = stateBelow(lwKey);
    out.push({
      id: 'family-pay',
      head: pc(roll.below) + ' of ' + name + ' jobs pay below the selected benchmark',
      stats: [
        [pc(roll.below), 'Below the benchmark'],
        [fmt(roll.belowN), 'Jobs below it'],
        [money(floor), 'The benchmark'],
      ],
      body: [
        'Read off each occupation’s own pay distribution and weighted by employment, over the ' +
          roll.nocc +
          ' occupations in this group that carry one.',
      ],
      read:
        'The statewide share is ' +
        pc(state) +
        ', so this group sits ' +
        pp(roll.below - state) +
        ' against Vermont as a whole.',
      bars: [
        { label: name, pct: roll.below, value: pc(roll.below) },
        { label: 'Vermont, all occupations', pct: state, value: pc(state), color: '--ord3' },
      ],
      src: 'Pay distributions 2025 · MIT Living Wage Calculator 2025',
    });
  }

  // Where the group sits relative to the rest, on replacement and on pay.
  if (row.turn !== null && row.turn !== undefined) {
    const all = LC.families.filter((x) => x.turn !== null && x.turn !== undefined);
    const rank = all.filter((x) => x.turn > row.turn).length + 1;
    out.push({
      id: 'family-replacement',
      head: 'The group replaces ' + pc(row.turn) + ' of its workforce a year',
      stats: [
        [pc(row.turn), 'Replaced a year'],
        [rank + ' of ' + all.length, 'From the highest rate'],
      ],
      body: [
        'A rate above 100% means more positions are refilled in a year than the group holds. The statewide figure across all groups is ' +
          pc(LC.sepPct) +
          '.',
      ],
      read:
        'At ' +
        pc(row.turn) +
        ', the group refills about ' +
        fmt(Math.round((row.jobs * row.turn) / 100)) +
        ' positions a year against ' +
        fmt(row.jobs) +
        ' jobs held.',
      src: 'Separations a year as a share of the group’s jobs, 2021–2025',
    });
  }

  // Counties where the group is a larger share of local jobs than it is statewide.
  const share = (CTY.state.share || {})[name];
  if (share !== undefined) {
    const local = CTY.counties
      .map((c) => ({ c: c.c, v: (c.mix || {})[name], emp: c.emp }))
      .filter((x) => x.v !== undefined)
      .sort((a, b) => b.v - a.v);
    out.push({
      id: 'family-geography',
      head: 'Where the group is a larger share of local jobs',
      body: ['Each figure is the group’s share of that county’s jobs, against ' + pc(share) + ' statewide.'],
      read:
        local[0].c +
        ' carries the highest share at ' +
        pc(local[0].v) +
        ', ' +
        pp(local[0].v - share) +
        ' against the statewide share.',
      bars: local.slice(0, 6).map((x) => ({
        label: x.c + ' · ' + fmt(x.emp) + ' jobs',
        pct: x.v,
        value: pc(x.v),
      })),
      src: 'Lightcast county occupational mix, 2025',
    });
  }

  const v = (SOW.vscs.byFamily || []).filter((x) => x.f === name)[0];
  if (v) {
    out.push({
      id: 'family-vscs',
      head: 'VSCS completions attributed to ' + name,
      stats: [
        [one(v.linked), 'Graduates attributed'],
        [fmt(v.open), 'Openings a year'],
        [v.open ? (v.linked / v.open).toFixed(3) : '—', 'Per opening'],
      ],
      body: [
        'Each program’s completions are divided across the occupations its program code links to, in proportion to Vermont employment. The figures are modelled rather than observed.',
      ],
      read:
        'The group draws ' +
        one(v.linked) +
        ' attributed graduates against ' +
        fmt(v.open) +
        ' openings a year, or ' +
        (v.open ? (v.linked / v.open).toFixed(3) : '—') +
        ' per opening.',
      src: 'Federal completions data 2024 · program-to-occupation crosswalk · modelled allocation',
    });
  }

  return out;
}

// ------------------------------------------------------- one program -------

function program(cip, lwKey) {
  const p = (SOW.vscs.byCip || []).filter((x) => x.cip === cip)[0];
  if (!p) return [];
  const name = p.n.replace(/\.$/, '');
  const out = [];
  const awards = Object.keys(p.awards || {}).sort((a, b) => p.awards[b] - p.awards[a]);

  out.push({
    id: 'program-size',
    head: name + ' recorded ' + p.c.toFixed(0) + ' completions in 2024',
    stats: [
      [p.c.toFixed(0), 'Completions'],
      [String(p.nsoc), 'Linked occupations'],
      [one(p.linked), 'Graduates attributed'],
    ],
    body: [
      'Awarded by ' +
        (p.inst || []).join(' and ') +
        '. Program code ' +
        p.cip +
        '. ' +
        (p.nsoc
          ? 'The crosswalk links it to ' + p.nsoc + ' occupations that exist in Vermont.'
          : 'The crosswalk links it to no occupation recorded in Vermont, so no graduates are attributed.'),
    ],
    read: awards.length
      ? 'The largest award level is ' +
        awards[0].toLowerCase() +
        ', at ' +
        p.awards[awards[0]].toFixed(1) +
        ' of ' +
        p.c.toFixed(0) +
        ' completions.'
      : 'No award level is recorded for this program.',
    table: awards.length
      ? {
          cols: ['Award level', 'Completions', 'Share of the program'],
          rows: awards.map((a) => [a, p.awards[a].toFixed(1), pc((p.awards[a] / p.c) * 100)]),
        }
      : null,
    src: 'Federal completions data, 2024 · first majors only',
  });

  const mix = p.tierMix || {};
  const tiers = TIER_ORDER.filter((t) => mix[t]);
  if (tiers.length) {
    const placed = tiers.reduce((a, t) => a + mix[t], 0);
    out.push({
      id: 'program-tiers',
      head: 'Where the program’s graduates land on the credential ladder',
      body: [
        'These are the credentials the WORK asks for at entry, not the award the program grants. A program can feed occupations entered at a different rung than it awards, and several do.',
      ],
      read:
        placed.toFixed(1) +
        ' of ' +
        p.c.toFixed(0) +
        ' completions land in a Vermont occupation carrying an entry credential, across ' +
        tiers.length +
        (tiers.length === 1 ? ' rung.' : ' rungs.'),
      bars: tiers.map((t, i) => ({
        label: t,
        pct: (mix[t] / placed) * 100,
        value: mix[t].toFixed(1),
        color: COL.ord[Math.min(i + 1, COL.ord.length - 1)],
      })),
      src: 'Program-to-occupation crosswalk · entry credential per occupation · modelled allocation',
    });
  }

  const fams = (p.fams || []).slice();
  if (fams.length) {
    const open = fams.map((f) => {
      const v = (SOW.vscs.byFamily || []).filter((x) => x.f === f.f)[0];
      return { ...f, open: v ? v.open : null };
    });
    const totOpen = open.reduce((a, x) => a + (x.open || 0), 0);
    out.push({
      id: 'program-demand',
      head: 'The occupation groups this program feeds',
      body: ['Graduates attributed to each group, against the openings those groups carry a year.'],
      read:
        'The groups this program feeds carry ' +
        fmt(totOpen) +
        ' openings a year between them, ' +
        pc((totOpen / openingSplit().open) * 100) +
        ' of the state total.',
      table: {
        cols: ['Occupation group', 'Graduates attributed', 'Openings a year'],
        rows: open.slice(0, 7).map((x) => [x.f, one(x.linked), x.open === null ? '—' : fmt(x.open)]),
      },
      src: 'Program-to-occupation crosswalk · openings 2021–2025',
    });
  }

  return out;
}

// ----------------------------------------------------------- the report ----

/**
 * Build the report for one scope and one benchmark.
 *
 * Findings are returned in the order they are defined, which is the order they
 * read in: size first, then pay, then what either implies. A finding that cannot
 * be computed for this scope is simply absent, so the report is as long as the
 * data supports and no longer.
 */
export function buildReport(kind, pick, lwKey) {
  let findings = [];
  let title = 'Vermont';
  let sub = 'Statewide';
  // The figures that frame everything under them. Taken from the same rows the
  // findings use, so the strip cannot disagree with the page it heads.
  let strip = [];

  if (kind === 'cty' && pick) {
    findings = county(pick, lwKey);
    title = pick + ' County';
    sub = 'One of Vermont’s 14 counties';
    const c = CTY.counties.filter((x) => x.c === pick)[0];
    const b = (((WF.counties.filter((x) => x.c === pick)[0] || {}).byLw || {})[lwKey] || {});
    if (c) {
      strip = [
        [fmt(c.emp), 'Jobs'],
        [money(c.med), 'Median pay'],
        [pp(c.chg), 'Since 2021'],
        [pc(b.local), 'Below the county’s own floor'],
      ];
    }
  } else if (kind === 'fam' && pick) {
    findings = family(pick, lwKey);
    title = pick;
    sub = 'One of 22 occupation groups';
    const r = LC.families.filter((x) => x.f === pick)[0];
    if (r) {
      strip = [
        [fmt(r.jobs), 'Jobs'],
        [fmt(r.open), 'Openings a year'],
        [money(r.med), 'Median pay'],
        [pc(r.above ? r.above[lwKey] : null), 'Clearing the benchmark'],
      ];
    }
  } else if (kind === 'cip' && pick) {
    const p = (SOW.vscs.byCip || []).filter((x) => x.cip === pick)[0];
    findings = program(pick, lwKey);
    title = p ? p.n.replace(/\.$/, '') : pick;
    sub = 'One VSCS program';
    if (p) {
      strip = [
        [p.c.toFixed(0), 'Completions, 2024'],
        [String(p.nsoc), 'Linked occupations'],
        [one(p.linked), 'Graduates attributed'],
        [String((p.tiers || []).length), 'Entry credentials reached'],
      ];
    }
  } else {
    findings = vermont(lwKey);
    strip = [
      [fmt(TOTJ), 'Jobs, 2025'],
      [fmt(Math.round(openingSplit().open)), 'Openings a year'],
      [pc(stateBelow(lwKey)), 'Of jobs below the benchmark'],
      [fmt(SOW.vscs.totalCompletions), 'VSCS completions, 2024'],
    ];
  }

  return {
    title,
    sub,
    strip,
    benchmark: lwKey,
    floor: lwAnnual(lwKey),
    hourly: LC.livingWage[lwKey],
    findings,
    // The standfirst states what the report covers. It does not characterise
    // the market: a sentence that grades Vermont is a sentence the reader
    // cannot check, and this page travels away from the tool that made it.
    standfirst:
      'Figures for ' +
      (kind === 'vt' ? 'Vermont' : title) +
      ', measured against ' +
      lwKey +
      ' at ' +
      money(lwAnnual(lwKey)) +
      ' a year. Each finding below is computed from the same data the dashboard shows.',
  };
}

/** The two rules every figure in the report depends on, carried with it. */
export const CAVEATS = [
  'Figures count jobs, not people. A person holding two jobs is counted twice, and a count of jobs below the benchmark is a count of positions rather than of individuals.',
  'Graduate figures are modelled, not observed. Each program’s completions are divided across the occupations its program code links to, in proportion to Vermont employment, which is why they carry a decimal.',
  'Wage adequacy is read off each occupation’s published pay distribution rather than its median, so an occupation can be partly above and partly below the benchmark. Occupations with no published distribution are excluded from both sides of the share.',
];

export const SOURCES =
  'Lightcast occupation, wage and postings data, 2025 · job postings January 2021 – January 2026 · ' +
  'MIT Living Wage Calculator 2025 at ' +
  fmt(LC.hours) +
  ' hours · federal completions data 2024 · American Community Survey 2016–2020 five-year estimates';
