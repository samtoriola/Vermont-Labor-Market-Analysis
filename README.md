# Vermont Labor Market Overview

Next.js dashboard covering all eight research questions from the Strada / VSCS
Vermont Labor Market Analysis scope of work.

## Run it

```bash
npm install
npm run dev
```

Then open http://localhost:3000.

## Deploy to Vercel

The app is entirely static — every figure is imported from JSON at build time, so
there are no environment variables, no service accounts and no runtime queries.

```bash
npx vercel
```

Or push to GitHub and import the repo at vercel.com/new. Framework preset is
detected automatically (Next.js); no build settings need changing.

## Layout

```
app/
  layout.js        fonts + metadata
  page.js          renders <Dashboard/>
  globals.css      design tokens, light + dark, all component styles
components/
  Dashboard.js     tab shell, living-wage state, methods footer
  Tooltip.js       shared hover/focus tooltip (React context)
  charts.js        RankedBars, BoxPlot, StackedRows, Dumbbell, TrendLine,
                   Scatter, GroupedBars, BoxLegend
  ui.js            Panel, Answer, Callout, QHead, Legend, Tiles, Table, LwPicker
  views/           Overview, Workers, and Q1…Q7 — one file per research question,
                   except Workers, which holds the panels that count people
                   rather than jobs
lib/
  data.js          imports the JSON, exports LC / PCT / DATA / SOW + helpers
  format.js        fmt, money, pct, niceMax, fmtVal
data/
  cps.json         CPS microdata aggregates, Vermont 2021–2025
  lightcast.json   occupation, industry, postings rollups
  percentiles.json wage percentile distributions
  sow.json         Q5 opportunity index, Q6 VSCS alignment, Q7 regions
  counties.json    jobs, pay and occupational mix for all 14 counties
  demand.json      what job postings ask for, by place
```

## How the navigation is grouped

By **what a figure counts**, not by where the number came from. The occupation
data counts jobs and job requirements; the household survey counts people and
what they hold. The two are not interchangeable, so the people panels are their
own group (Workers) rather than sitting beside jobs panels under Wage quality
and Pathways, where a reader changed unit without being told.

## Regenerating the data

The JSON files are build outputs, not hand-edited. The pipeline lives in `scripts/`
and queries BigQuery (`strada-data-lab-c9d1`) plus the Lightcast CSV exports in
`G:\My Drive\Vermont Labor Market Analysis`:

| Script | Produces |
| --- | --- |
| `get_lw.py` | `vt_living_wage.csv` — MIT benchmarks (committed; rarely re-run) |
| `cps_vt_extract.py` → `make_js.py` | `cps.json` — CPS Vermont aggregates |
| `build.py` | `lightcast.json` — occupation / industry / postings rollups |
| `build_pct.py` | `percentiles.json` — wage percentile distributions |
| `build_sow.py` | `sow.json` — opportunity index, VSCS alignment, regions |
| `pull_counties.py` | **one-off** — Core LMI county slice to the Drive folder |
| `pull_postings.py` | **one-off** — postings education/experience by place to the Drive folder |
| `build_demand.py` | `demand.json` — what postings ask for, by place |
| `build_counties.py` | `counties.json` — county jobs, pay and occupational mix |
| `mk_app_data.py` | copies all four into `data/` |
| `verify_app.py` | structural check of the app (stands in for `next build`) |

**See [`scripts/README.md`](scripts/README.md)** for the exact run order, BigQuery auth
setup (including the `--disable-quota-project` flag you must use), the inputs each script
expects, and the analytical decisions baked into them — the openings divisor, the
living-wage default, the Q5 composite, and the Q6 allocation assumption.

Re-run them, then commit the refreshed JSON. Nothing in the app queries BigQuery
directly.

## Things to know before presenting this

- **It is a mockup.** The living-wage benchmark, the opportunity-index weights and
  the regional definitions are all decisions the SOW (section 7) assigns to VSCS.
  The benchmark is a live control in the UI; the weights are equal by default.
- **Lightcast and CPS measure different things.** Lightcast counts jobs and job
  requirements; CPS counts employed residents and what they hold. Compare shares,
  never levels.
- **Research question 7 is answered on both sides now.** Regional attainment and
  wage sufficiency were always there by county; occupational demand and pay by region
  were not, because every Lightcast CSV export is statewide. The Core LMI county slice
  closes it, and the Regions tab reads it: county employment, the pay of the midpoint
  job, change since 2021, and what each county is concentrated in against the state.
  **Use classes 1+2** (QCEW + non-QCEW employees) — they reproduce the statewide total
  to 0.009%, where summing all four classes lands 40% high.
- **A county location quotient is a ratio of shares, not a size.** Essex at 6.9× the
  state concentration in farming is sixty-three jobs. The grid prints the figure only
  on its top step, puts the job count on every hover, and outlines the two counties
  (Essex and Grand Isle) too small to split twenty-two ways.
- **The openings figure carries one assumption** — Lightcast's `2021 - 2025 Openings`
  divided by 4. If that window is meant inclusively as five years, every openings
  number scales down by a fifth.

The in-app methods footer carries the full set of caveats, including the CIP-to-SOC
allocation assumption behind Q6 and the composite-index derivation behind Q5.
