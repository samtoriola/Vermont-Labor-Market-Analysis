"""Home tiles cite their source on hover, and About stops reading CPS for a
Lightcast count.

The four headline figures come from four different places and two different
universes -- jobs from Lightcast, people from the CPS -- and until now the tiles
said neither. There is no room on a tile for a source line without crowding out
the figure, so it goes on hover, the way every chart's marks already work.

Checks every substitution before writing anything: a patch that applies three of
four and then throws leaves the files untouched but the edits lost.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
EDITS = []


def edit(rel, pairs):
    EDITS.append((rel, pairs))


# ------------------------------------------------------------------ ui.js ---
edit("components/ui.js", [
    ("import DataTable from './DataTable';",
     "import DataTable from './DataTable';\nimport { useTip } from './Tooltip';"),
    ("""export function Tiles({ items }) {
  return (
    <div className="tiles">
      {items.map((t) => (
        <div className="tile" key={t[0]}>
          <div className="tl">{t[0]}</div>
          <div className="tv">{t[1]}</div>
          <div className="td">{t[2]}</div>
        </div>
      ))}
    </div>
  );
}""",
     """/**
 * The headline figures. A tile may carry a fourth element saying where its figure
 * came from -- { counts, rows, foot } -- which shows on hover rather than on the
 * card: a tile has room for a number and one line of context, and a source line
 * under each would crowd out both. The badge is the only cue that hovering does
 * anything, and without it the source is there and nobody finds it.
 */
export function Tiles({ items }) {
  const { show, hide } = useTip();
  return (
    <div className="tiles">
      {items.map((t) => {
        const s = t[3];
        const on = s
          ? {
              tabIndex: 0,
              onMouseMove: (e) => show(e, t[0], s.rows, { sub: s.counts, foot: s.foot }),
              onMouseLeave: hide,
              onFocus: (e) => {
                const b = e.currentTarget.getBoundingClientRect();
                show({ clientX: b.left + b.width / 2, clientY: b.bottom }, t[0], s.rows, {
                  sub: s.counts,
                  foot: s.foot,
                });
              },
              onBlur: hide,
            }
          : {};
        return (
          <div className={s ? 'tile cited' : 'tile'} key={t[0]} {...on}>
            {s ? (
              <span className="tcite" aria-hidden="true">
                i
              </span>
            ) : null}
            <div className="tl">{t[0]}</div>
            <div className="tv">{t[1]}</div>
            <div className="td">{t[2]}</div>
          </div>
        );
      })}
    </div>
  );
}"""),
])

# ------------------------------------------------------------- globals.css ---
edit("app/globals.css", [
    ("/* ---------- charts ---------- */",
     """/* A tile carrying its source. The badge is the cue that hovering does something;
   the source is on hover because the card has no room for a line of provenance. */
.tile.cited {
  position: relative;
  cursor: help;
}

.tile.cited .tl {
  padding-right: 22px;
}

.tile.cited .tcite {
  position: absolute;
  top: 9px;
  right: 10px;
  width: 13px;
  height: 13px;
  border: 1px solid var(--rule-strong);
  border-radius: 50%;
  color: var(--ink-3);
  font-family: var(--fig);
  font-size: 9px;
  font-style: italic;
  font-weight: 700;
  line-height: 12px;
  text-align: center;
}

.tile.cited:hover .tcite,
.tile.cited:focus-visible .tcite {
  border-color: var(--accent);
  color: var(--accent);
}

.tile.cited:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* ---------- charts ---------- */"""),
])

# ----------------------------------------------------------------- Home.js ---
edit("components/views/Home.js", [
    ("""  const tiles = [
    ['Jobs, 2025', fmt(TOTJ), fmt(LC.allOcc.length) + ' occupations'],
    ['Employed Vermonters', fmt(GLANCE.emp), GLANCE.year + ', monthly average'],
    ['Annual openings', fmt(LC.openTotal / LC.openYears), LC.window],
    ['VSCS completions', fmt(SOW.vscs.totalCompletions), '2024, ' + SOW.vscs.nCip + ' programs'],
  ];""",
     """  // The export's statewide total runs above what the charted occupations sum to:
  // military work and SOCs outside the 22 groups are dropped from every chart. The
  // tile prints the larger figure, so the smaller one belongs in its source card.
  const charted = LC.allOcc.reduce((a, o) => a + (o.j || 0), 0);
  const FOOT = 'Methods lists every source and what each chart uses';

  // Four figures, four sources, two universes -- jobs and people, which do not add
  // together. Each tile says which it is on hover.
  const tiles = [
    [
      'Jobs, 2025',
      fmt(TOTJ),
      fmt(LC.allOcc.length) + ' occupations',
      {
        counts: 'Jobs located in Vermont, not people. Someone holding two counts twice.',
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
          'Openings a year, including replacing people who leave \\u2014 not only new jobs.',
        rows: [
          ['Source', 'Vermont occupation data'],
          ['Vintage', LC.window],
          ['Arithmetic', fmt(LC.openTotal) + ' \\u00f7 ' + LC.openYears],
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
  ];"""),
])

# ---------------------------------------------------------------- About.js ---
edit("components/views/About.js", [
    ("import { LC, TOTJ, DATA, SOW, GLANCE } from '@/lib/data';",
     "import { LC, TOTJ, SOW, GLANCE } from '@/lib/data';"),
    ("${fmt(LC.allOcc.length)} detailed occupations, ${fmt(DATA.families.length)} occupation groups",
     "${fmt(LC.allOcc.length)} detailed occupations, ${fmt(LC.families.length)} occupation groups"),
    ("The Census surveys count people, and are used here only for what a county\\u2019s residents hold and earn, on the Regions map.",
     "The Census surveys count people, and reach two figures: employed Vermonters, on the home page, and what a county\\u2019s residents hold and earn, on the Regions map."),
    ("""              'Check where a number came from',
              'Every chart carries a source line underneath it, written in plain words rather than by vendor. Methods holds the key""",
     """              'Check where a number came from',
              'Every chart carries a source line underneath it, written in plain words rather than by vendor, and each of the four tiles on the home page carries its own on hover — source, vintage, the file the app reads, and the workfile that reproduces it. Methods holds the key"""),
])

# -------------------------------------------------------------- Methods.js ---
edit("components/views/Methods.js", [
    # A register row for the home page, which the register has never had.
    ("""          rows={[
            {
              cells: [
                'Overview',""",
     """          rows={[
            {
              cells: [
                'Home',
                'Four headline tiles, each citing its source on hover',
                'Lightcast occupations · Census household survey · IPEDS',
                'lightcast.json, glance.json, sow.json',
                '14_home_tiles.csv',
              ],
            },
            {
              cells: [
                'Overview',"""),
    # The CPS row now has a workfile of its own.
    ("""                'Vermont monthly microdata. Reaches one figure: the employed-Vermonters tile on the home page',""",
     """                'Vermont monthly microdata. Reaches one figure on screen: the employed-Vermonters tile on the home page, which 15_labor_force_cps.csv carries in full',"""),
    # And the two job totals, which nothing has ever explained.
    ("""            [
              'Rates need a real base',""",
     """            [
              'Two job totals',
              'The home page prints 326,582 jobs and every chart totals 325,132. The difference is 1,450 jobs in military occupations and in SOC codes falling outside the 22 occupation groups, which the exports carry in the statewide total and the charts drop, because neither has an occupation group, a credential or a pay ladder to sit under. It is 0.4% of employment, and it is why group shares read off a chart will not quite reproduce against the tile.',
            ],
            [
              'Rates need a real base',"""),
])

# ------------------------------------------------------------------ apply ---
loaded = []
for rel, pairs in EDITS:
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _ in pairs:
        if s.count(old) != 1:
            raise SystemExit("%s: %d occurrences of %r" % (rel, s.count(old), old[:90]))
    loaded.append((p, rel, s, pairs))

for p, rel, s, pairs in loaded:
    for old, new in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("%-32s %d edits, %d bytes" % (rel, len(pairs), len(s)))
