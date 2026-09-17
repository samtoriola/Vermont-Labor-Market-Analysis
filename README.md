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
  views/           Overview + Q1…Q8, one file per research question
lib/
  data.js          imports the JSON, exports LC / PCT / DATA / SOW + helpers
  format.js        fmt, money, pct, niceMax, fmtVal
data/
  cps.json         CPS microdata aggregates, Vermont 2021–2025
  lightcast.json   occupation, industry, postings rollups
  percentiles.json wage percentile distributions
  sow.json         Q5 opportunity index, Q6 VSCS alignment, Q7 regions
```

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
- **Research question 7 is half-answered.** Regional attainment and wage sufficiency
  are present by county; occupational demand and wage premiums by region are not,
  because both Lightcast exports are statewide. Lightcast Core LMI covers all 14
  Vermont counties and would close the gap.
- **The openings figure carries one assumption** — Lightcast's `2021 - 2025 Openings`
  divided by 4. If that window is meant inclusively as five years, every openings
  number scales down by a fifth.

The in-app methods footer carries the full set of caveats, including the CIP-to-SOC
allocation assumption behind Q6 and the composite-index derivation behind Q5.
