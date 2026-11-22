"""Review 11/18, Wage benchmark: a credential filter beside the benchmark.

Not the Rows option of the same name. Rows draws one bar PER tier and answers
"which credential level pays worst". This narrows every row to the work entered
at one tier and answers "inside sub-baccalaureate work, which occupation groups
pay worst" -- a question the tab could not ask at all, because its two controls
both chose what the rows were rather than which occupations were in them.

The old comment above <ActiveFilters /> argued against exactly this: "a credential
filter on a chart of credentials is a chart with rows missing". That is true, and
it is why picking a tier drops the credential ROWS option rather than drawing a
single bar. It is not a reason to withhold the filter from the other three row
options, which is what the comment was being used for.

The Rows option has to be dropped rather than left to degenerate, so `a` is
computed from the tier.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "components", "views", "Q2.js")
s = io.open(P, encoding="utf-8").read()

subs = [
    # ---- the option list --------------------------------------------------
    ("const BENCH = [",
     """// The filter, as distinct from the Rows option. See the note at the top of the
// credential Picker below for why picking one here removes the other.
const CREDS = [{ id: 'all', label: 'All credentials' }].concat(
  TIER_ORDER.map((t) => ({ id: t, label: t }))
);

const BENCH = ["""),

    # ---- the scoped figures move into the render --------------------------
    ("""  const head = rollUp(filtered, LWA);

  // The scatter's rows: one point per occupation that has a median to plot. The
  // count of those falling short is of OCCUPATIONS, not jobs -- a point is one
  // occupation whatever its size, which is the whole reason the y-axis exists.
  const plotted = filtered.filter((o) => o.m);
  const shortOcc = plotted.filter((o) => o.m < LWA).length;""",
     """  // The tab headline stays over everything priced: it is above the controls and
  // describes the state, not whatever the reader has narrowed to.
  const head = rollUp(filtered, LWA);"""),

    # ---- rowsFor takes its rows -------------------------------------------
    ("""  const rowsFor = (kind) => {
    if (kind === 'group') {
      return rollUpBy(filtered, (o) => o.f, LWA).map((r) => ({""",
     """  const rowsFor = (kind, rows) => {
    if (kind === 'group') {
      return rollUpBy(rows, (o) => o.f, LWA).map((r) => ({"""),

    ("""      return rollUpBy(filtered, (o) => o.t, LWA)""",
     """      return rollUpBy(rows, (o) => o.t, LWA)"""),

    ("""    return filtered
      .slice()
      .sort((a, b) => b.j - a.j)
      .slice(0, 25)""",
     """    return rows
      .slice()
      .sort((a, b) => b.j - a.j)
      .slice(0, 25)"""),

    # ---- src becomes a function of the scope ------------------------------
    ("""  const src =
    `Vermont occupation data, 2025 · ${fmt(head ? head.jobs : 0)} jobs with a published pay ` +
    `distribution · benchmark ${money(LWA)} a year (${lw}) · the benchmark's position read off ` +
    `each occupation's own 10th-to-90th percentile ladder, weighted by its jobs`;""",
     """  const srcFor = (h, tier) =>
    `Vermont occupation data, 2025 · ${fmt(h ? h.jobs : 0)} jobs with a published pay ` +
    `distribution${tier === 'all' ? '' : `, entered at ${tier.toLowerCase()}`} · benchmark ` +
    `${money(LWA)} a year (${lw}) · the benchmark's position read off each occupation's own ` +
    `10th-to-90th percentile ladder, weighted by its jobs`;"""),

    # ---- the picker wraps the pair ----------------------------------------
    ("""                <ActiveFilters />
                <PickerPair
                  id="q2-rows"
                  aLabel="Rows"
                  a={ROWS}
                  bLabel="Measure"
                  b={MEASURES}
                  hideB={(kind) => kind === 'each'}
                >
                  {(kind, measure) =>""",
     """                <ActiveFilters />
                <Picker id="q2-cred" label="Credential" options={CREDS}>
                  {(tier) => {
                    const scoped =
                      tier === 'all' ? filtered : filtered.filter((o) => o.t === tier);
                    const sHead = rollUp(scoped, LWA);
                    const src = srcFor(sHead, tier);
                    // One point per occupation with a median. The count falling
                    // short is of OCCUPATIONS, not jobs -- a point is one
                    // occupation whatever its size.
                    const plotted = scoped.filter((o) => o.m);
                    const shortOcc = plotted.filter((o) => o.m < LWA).length;
                    return (
                <PickerPair
                  id="q2-rows"
                  aLabel="Rows"
                  a={tier === 'all' ? ROWS : ROWS.filter((r) => r.id !== 'cred')}
                  bLabel="Measure"
                  b={MEASURES}
                  hideB={(kind) => kind === 'each'}
                >
                  {(kind, measure) =>"""),

    # ---- the scatter caption and rows -------------------------------------
    ("""                        cap={`${filtered.length === pool.length ? fmt(pool.length) : `${fmt(filtered.length)} of ${fmt(pool.length)}`} occupations, one point each.""",
     """                        cap={`${scoped.length === pool.length ? fmt(pool.length) : `${fmt(scoped.length)} of ${fmt(pool.length)}`} occupations, one point each."""),

    ("""                          cols: occCols(LWA),
                          rows: filtered,""",
     """                          cols: occCols(LWA),
                          rows: scoped,"""),

    ("""                        const rows = rowsFor(kind);""",
     """                        const rows = rowsFor(kind, scoped);"""),

    # ---- close the new picker ---------------------------------------------
    ("""                    )
                  }
                </PickerPair>
              </>
            ),
          },""",
     """                    )
                  }
                </PickerPair>
                    );
                  }}
                </Picker>
              </>
            ),
          },"""),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("%d occurrences of %r" % (s.count(old), old[:80]))
for old, new in subs:
    s = s.replace(old, new)

# TIER_ORDER has to be in scope for CREDS.
if "TIER_ORDER" not in s.split("\n")[2]:
    s = s.replace(
        "import { LC, TIER_ORDER, WF, lwAnnual, occByFamily } from '@/lib/data';",
        "import { LC, TIER_ORDER, WF, lwAnnual, occByFamily } from '@/lib/data';")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Q2.js patched,", len(s), "bytes")
