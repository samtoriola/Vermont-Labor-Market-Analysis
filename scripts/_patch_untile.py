"""Takes the hover cards back off the home tiles.

They crowded the landing page: four badges across the top row and a card that
covers two of the topic cards the moment the pointer crosses a tile. The
provenance itself stays -- in Methods' register, in 14_home_tiles.csv and in
15_labor_force_cps.csv -- so nothing is lost except the hover, and nothing is
left claiming a hover that is no longer there.

Checks every substitution before writing anything.
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
    ("import DataTable from './DataTable';\nimport { useTip } from './Tooltip';",
     "import DataTable from './DataTable';"),
    ("""/**
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
}""",
     """/**
 * The headline figures. Deliberately plain: a tile is a number and one line of
 * context, and anything more on it -- a source, a badge, a card on hover -- turns
 * the first thing on the page into the busiest. Where each figure comes from is
 * in Methods' register and in workfiles/14_home_tiles.csv.
 */
export function Tiles({ items }) {
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
}"""),
])

# ------------------------------------------------------------- globals.css ---
edit("app/globals.css", [
    ("""/* A tile carrying its source. The badge is the cue that hovering does something;
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

/* ---------- charts ---------- */""",
     "/* ---------- charts ---------- */"),
])

# ----------------------------------------------------------------- Home.js ---
with io.open(os.path.join(H, "..", "components", "views", "Home.js"), encoding="utf-8") as f:
    home = f.read()
start = home.index("  // The export's statewide total")
end = home.index("  ];", start) + len("  ];")
edit("components/views/Home.js", [
    (home[start:end],
     """  const tiles = [
    ['Jobs, 2025', fmt(TOTJ), fmt(LC.allOcc.length) + ' occupations'],
    ['Employed Vermonters', fmt(GLANCE.emp), GLANCE.year + ', monthly average'],
    ['Annual openings', fmt(LC.openTotal / LC.openYears), LC.window],
    ['VSCS completions', fmt(SOW.vscs.totalCompletions), '2024, ' + SOW.vscs.nCip + ' programs'],
  ];"""),
])

# ---------------------------------------------------------------- About.js ---
edit("components/views/About.js", [
    ("'Every chart carries a source line underneath it, written in plain words rather than by vendor, and each of the four tiles on the home page carries its own on hover — source, vintage, the file the app reads, and the workfile that reproduces it. Methods holds the key",
     "'Every chart carries a source line underneath it, written in plain words rather than by vendor. The home page's four tiles are the exception, and carry no source line; Methods' register has a row for them, as it does for every section. Methods holds the key"),
])

# -------------------------------------------------------------- Methods.js ---
edit("components/views/Methods.js", [
    ("'Four headline tiles, each citing its source on hover',",
     "'Four headline tiles. Two count jobs, one counts people, one counts credentials',"),
])

# ------------------------------------------------------- build_workfiles.py ---
edit("scripts/build_workfiles.py", [
    ('''    "Home. One row per headline tile, which is what that tile's hover card says: "
    "source, vintage, the file the app reads and the workfile that reproduces it. "''',
     '''    "Home. One row per headline tile: source, vintage, the file the app reads and "
    "the workfile that reproduces it. The tiles themselves carry no source line -- "
    "this file and the Methods register are where that lives. "'''),
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
