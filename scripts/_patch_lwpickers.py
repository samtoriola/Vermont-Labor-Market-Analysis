"""Review 11/18: the benchmark picker on the tabs that were missing it, a
credential filter on Wage benchmark, and two more columns on the industry drill.

WHERE THE PICKER GOES. "All tabs and subtabs where the filter makes sense" is the
operative clause. It goes on Employment / Occupation and on VSCS alignment /
Against demand, because both price their drill-downs against the benchmark and
both were reading it without being able to set it. It does NOT go on Employment /
Industry sectors (industry pay is a mean per job, with no ladder to place a
benchmark on), on Demand / General demand (postings education and experience have
no pay in them at all), or on Home, About and Methods. A control that changes
nothing on screen is worse than no control: it teaches the reader that the
controls do not matter.

WAGE BENCHMARK gets the credential filter the review asked for, beside the
benchmark. Note it is a filter, not the existing Rows option of the same name:
Rows draws one bar per tier, this narrows every row to the work entered at one.

INDUSTRY DRILL. Average pay per job was already on it. Turnover was not and
cannot be: data/lightcast.json's industry records carry naics, name, sector, jobs
and earnings and no separations at all -- that measure exists only by occupation
in this export. Share of the sector and share of the state go on instead, which
are the two the table was actually missing.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

EDITS = {
    # --------------------------------------------------------------- Q1 ----
    "components/views/Q1.js": [
        ("import { HowTo, Panel, Legend, Picker, Ranked, RampLegend, Scope, VHead, DrillHint } from '../ui';",
         "import { HowTo, LwPicker, Panel, Legend, Picker, Ranked, RampLegend, Scope, VHead, DrillHint } from '../ui';", 1),
        ("export default function Q1({ lw, section }) {",
         "export default function Q1({ lw, setLw, section }) {", 1),
        ("""                  The same 22 occupation groups under every measure — jobs, pay, what they ask
                  for at the door, and who is doing them. Click a bar for the occupations
                  inside it.
                </HowTo>
                <Picker id="q1-fam" label="Measure" options={FAM_MEASURES}>""",
         """                  The same 22 occupation groups under every measure — jobs, pay, what they ask
                  for at the door, and who is doing them. Click a bar for the occupations
                  inside it, priced against the benchmark below.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                <Picker id="q1-fam" label="Measure" options={FAM_MEASURES}>""", 1),
    ],
    # --------------------------------------------------------------- Q6 ----
    "components/views/Q6.js": [
        ("import { Callout, HowTo, Panel, Picker, Ranked, VHead, N } from '../ui';",
         "import { Callout, HowTo, LwPicker, Panel, Picker, Ranked, VHead, N } from '../ui';", 1),
        ("export default function Q6({ lw, section }) {",
         "export default function Q6({ lw, setLw, section }) {", 1),
        ("""                  which no figure on this dashboard can tell you.
                </HowTo>
                <Picker id="q6-level" label="Level" options={LEVELS}>""",
         """                  which no figure on this dashboard can tell you.
                </HowTo>
                <LwPicker value={lw} onChange={setLw} />
                <Picker id="q6-level" label="Level" options={LEVELS}>""", 1),
    ],
}

loaded = []
for rel, pairs in EDITS.items():
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _, want in pairs:
        if s.count(old) != want:
            raise SystemExit("%s: %d of %r, expected %d" % (rel, s.count(old), old[:60], want))
    loaded.append((p, rel, s, pairs))

for p, rel, s, pairs in loaded:
    for old, new, _ in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("%-28s patched" % rel)

# ------------------------------------------------------- the industry drill --
T = os.path.join(H, "..", "lib", "tables.js")
t = io.open(T, encoding="utf-8").read()
old = """export function industryCols() {
  return [
    { k: 'n', label: 'Industry', kind: 'text', get: (r) => r.n },
    { k: 'naics', label: 'Industry code', kind: 'text', get: (r) => r.naics },
    { k: 'j', label: 'Jobs', kind: 'num', get: (r) => r.j },
    { k: 'earn', label: 'Average pay per job', kind: 'money', get: (r) => r.earn },
  ];
}"""
new = """export function industryCols(secJobs) {
  return [
    { k: 'n', label: 'Industry', kind: 'text', get: (r) => r.n },
    { k: 'naics', label: 'Industry code', kind: 'text', get: (r) => r.naics },
    { k: 'j', label: 'Jobs', kind: 'num', get: (r) => r.j },
    { k: 'sec', label: 'Share of the sector', kind: 'rate',
      get: (r) => (secJobs ? (r.j / secJobs) * 100 : null) },
    { k: 'share', label: 'Share of all jobs', kind: 'rate', get: (r) => (r.j / TOTAL_JOBS) * 100 },
    { k: 'earn', label: 'Average pay per job', kind: 'money', get: (r) => r.earn },
  ];
}"""
if t.count(old) != 1:
    raise SystemExit("tables.js: %d occurrences of industryCols" % t.count(old))
io.open(T, "w", encoding="utf-8", newline="").write(t.replace(old, new))
print("%-28s patched" % "lib/tables.js")

# The one call site has to hand it the sector's size, or the new column is null.
Q = os.path.join(H, "..", "components", "views", "Q1.js")
q = io.open(Q, encoding="utf-8").read()
if q.count("      cols: industryCols(),") != 1:
    raise SystemExit("Q1.js: industryCols() call site not found exactly once")
q = q.replace("      cols: industryCols(),", "      cols: industryCols(r.j),")
io.open(Q, "w", encoding="utf-8", newline="").write(q)
print("%-28s industryCols(r.j)" % "components/views/Q1.js")
