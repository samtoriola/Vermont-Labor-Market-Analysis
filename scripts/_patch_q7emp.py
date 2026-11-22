"""The county panel gains who advertises there, and in what.

Two lists under the figures, from data/county_postings.json. They answer the
review's "top 5 employers, top 5 industry" as closely as the data honestly can,
which is not all the way: these are postings, so they say who ADVERTISES, not who
EMPLOYS. The panel says so in the line under them rather than in Methods alone,
because the gap is large enough to mislead someone who only reads the panel --
Cardinal Health tops Washington County on 818 postings while the State of Vermont,
the county's obvious largest employer, sits second.

Explicitly remote roles are already excluded in the build, which is what let
Chittenden read sensibly at all: before that filter Washington County outranked
it on 6,456 remote postings filed from Montpelier addresses against Chittenden's
750, in a county a third its size.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- data.js ---
P = os.path.join(H, "..", "lib", "data.js")
s = io.open(P, encoding="utf-8").read()
subs = [
    ("import wagefloor from '@/data/wagefloor.json';",
     "import wagefloor from '@/data/wagefloor.json';\nimport countyPostings from '@/data/county_postings.json';"),
    ("export const WF = wagefloor; // Each county's jobs against its own cost floor",
     "export const WF = wagefloor; // Each county's jobs against its own cost floor\n"
     "export const CPOST = countyPostings; // Who advertises in each county, and in what"),
]
for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("data.js: %d of %r" % (s.count(old), old[:60]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("lib/data.js patched")

# ------------------------------------------------------------------ Q7.js ---
P = os.path.join(H, "..", "components", "views", "Q7.js")
s = io.open(P, encoding="utf-8").read()

subs = [
    ("import { Callout, HowTo, Legend, Panel, Picker, VHead, LwPicker, N } from '../ui';",
     "import { Callout, HowTo, Legend, Panel, Picker, VHead, LwPicker, N } from '../ui';\n"
     "import { CPOST } from '@/lib/data';"),

    ("""        <p className="cap" style={{ margin: 0 }}>
          Vermont for comparison: <N>{wBa.toFixed(1)}%</N> BA+ (population-weighted),
          a typical job at <N>{money(ST.med)}</N>, living wage <N>$23.95</N>/hr statewide.
        </p>
      </Panel>""",
     """        <p className="cap" style={{ margin: 0 }}>
          Vermont for comparison: <N>{wBa.toFixed(1)}%</N> BA+ (population-weighted),
          a typical job at <N>{money(ST.med)}</N>, living wage <N>$23.95</N>/hr statewide.
        </p>
        {posts(picked.c)}
      </Panel>"""),

    # The two lists, and the sentence that keeps them honest.
    ("""  // Every county-and-family pair, the figures behind the grid. One row each
  // rather than a 22-column table nobody can read on a laptop.""",
     """  /**
   * Who advertises in a county, and in what.
   *
   * POSTINGS, NOT PAYROLL. This is the only place on the dashboard that names an
   * employer, and the temptation is to read it as "the biggest employers here".
   * It is not that and cannot be made into that from this data: a posting counts
   * once however many people it hires, an employer that never advertises never
   * appears, and the county on a posting is where the company filed it. The
   * caption says so in the panel rather than only in Methods, because someone
   * who reads nothing else will read this.
   *
   * Lightcast resolves a company name per posting and does not always resolve the
   * same employer to one name -- Chittenden shows both "The University Of Vermont
   * Me(dical Center)" and "Uvm Medical Center" -- so the ranking is of names, not
   * of legal entities.
   */
  const posts = (name) => {
    const k = Object.keys(CPOST.counties).filter(
      (id) => CPOST.counties[id].c === name
    )[0];
    const d = k ? CPOST.counties[k] : null;
    if (!d || (!d.employers.length && !d.industries.length)) return null;
    const list = (title, items) => (
      <div className="pcol">
        <div className="k">{title}</div>
        <ol className="plist">
          {items.map((x) => (
            <li key={x.n}>
              <span className="pn">{x.n}</span>
              <span className="pv">{fmt(x.p)}</span>
            </li>
          ))}
        </ol>
      </div>
    );
    return (
      <>
        <div className="pcols">
          {list('Advertises most', d.employers)}
          {list('Most advertised industries', d.industries)}
        </div>
        <p className="cap" style={{ margin: 0 }}>
          Job postings, {CPOST.window}, {fmt(d.postings)} in this county — who{' '}
          <strong>advertises</strong>, not who employs. One posting counts once however
          many people it hires, and an employer that rarely advertises does not appear.
          Explicitly remote roles are excluded: a posting carries the county the employer
          filed it from, which puts national employers in the county holding their
          registered address.
        </p>
      </>
    );
  };

  // Every county-and-family pair, the figures behind the grid. One row each
  // rather than a 22-column table nobody can read on a laptop."""),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("Q7.js: %d occurrences of %r" % (s.count(old), old[:70]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("components/views/Q7.js patched")

# -------------------------------------------------------------- globals.css --
P = os.path.join(H, "..", "app", "globals.css")
css = io.open(P, encoding="utf-8").read()
anchor = "/* ---------- charts ---------- */"
block = """/* The two postings lists in the county panel. Ranked, so they are an ol, and
   the count sits right so the names stay scannable down the left. */
.pcols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin: 14px 0 10px;
}

@media (max-width: 720px) {
  .pcols {
    grid-template-columns: 1fr;
  }
}

.pcol .k {
  color: var(--ink-3);
  font-family: var(--fig);
  font-size: 10px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.plist {
  list-style: none;
  margin: 0;
  padding: 0;
}

.plist li {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 3px 0;
  border-bottom: 1px solid var(--rule);
  font-size: 13px;
}

.plist li:last-child {
  border-bottom: 0;
}

.plist .pn {
  flex: 1;
  min-width: 0;
}

.plist .pv {
  color: var(--ink-2);
  font-family: var(--fig);
  font-variant-numeric: tabular-nums;
}

/* ---------- charts ---------- */"""
if css.count(anchor) != 1:
    raise SystemExit("globals.css: %d anchors" % css.count(anchor))
io.open(P, "w", encoding="utf-8", newline="").write(css.replace(anchor, block))
print("app/globals.css patched")
