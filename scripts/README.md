# Data pipeline

These scripts regenerate the four JSON files in `../data/`. The app never queries
anything at runtime — it imports those JSONs at build time — so this is the only way
the numbers change.

## Setup

```bash
pip install -r requirements.txt
gcloud auth application-default login --disable-quota-project
```

The `--disable-quota-project` flag matters. Setting a quota project on these accounts
causes every BigQuery request to return 403, because our IAM roles lack
`serviceusage.services.use`. If that has already happened, the command above is also
the recovery.

Do **not** install `google-cloud-bigquery-storage`. Our roles lack
`bigquery.readsessions.create`, and with that package present `.to_dataframe()` hard-fails
with 403 instead of falling back to REST.

## Inputs

Two kinds. BigQuery (project `strada-data-lab-c9d1`):

| Dataset / table | Used for |
| --- | --- |
| `monthly_cps.cps` | CPS Vermont microdata, 2021–2025 |
| `ipeds.2024_Completions_AwardsByCIP_C2024_A` | VSCS completions |
| `cip_soc_crosswalk.cip2020_soc2018_crosswalk` | CIP → SOC mapping |
| `census_bureau_acs.county_2020_5yr` | County attainment and income |
| `sandbox.mit_living_wage_2025` | Living-wage benchmarks |

And three Lightcast CSV exports, expected in the parent Drive folder
(`G:\My Drive\Vermont Labor Market Analysis`), referenced by the `FOLDER` constant at
the top of `build.py`, `build_pct.py` and `build_sow.py`:

- `Occupation_Table_All_Occupations_in_Vermont_37191a85abaf7e4a_Updated.csv` — the
  window-consistent export: 2021/2025 jobs, `2021 - 2025 Openings`, annual wage
  percentiles, entry education, projections to 2030
- `Occupation_Table_All_Occupations_in_Vermont_947ddfb5a42985dc.csv` — carried forward
  **only** for `2025 Employment Concentration`, which the updated export omits
- `Industry_Table_All_Industries_in_Vermont_2f9f3aeb90250b18.csv`
- `Job_Postings_Table_Vermont_46d10895226907a6.csv`

If Lightcast re-exports under new hashed filenames, update those constants.

## Run order

```bash
python get_lw.py           # -> vt_living_wage.csv   (BigQuery; needed by build.py, build_sow.py)
python cps_vt_extract.py   # -> cps_vt_dashboard_data.json
python make_js.py          # -> dash_data.js
python build.py            # -> lc_data.js
python build_pct.py        # -> pct_data.js
python build_sow.py        # -> sow_data.js          (BigQuery + CSVs)
python mk_app_data.py      # -> ../data/*.json
python verify_app.py       # structural check of the app
```

`vt_living_wage.csv` is committed, so `get_lw.py` only needs re-running if MIT publishes
a new year.

## Decisions baked into these scripts

Change them here, not in the app.

- **`OPEN_YEARS = 4`** in `build.py` and `build_sow.py`. Lightcast's
  `2021 - 2025 Openings` is a cumulative total; 4 matches how Lightcast computes
  `2021 - 2025 Change` (an endpoint difference across four intervals). If that window is
  meant inclusively as five years, change it to 5 and every openings figure drops a fifth.
- **`LW_DEFAULT = 23.95 * 2080`** in `build_sow.py` — one adult, no children. The app
  exposes all eight household types as a live selector; this constant only sets the
  default and the Q5 context columns.
- **Q5 composite** in `build_sow.py`: four components at 25% each — employment, projected
  growth, postings per 100 jobs, median pay. Two earlier components were removed after
  measurement: living-wage ratio (rank-identical to pay, r = 1.000, because the benchmark
  is a constant) and openings intensity (correlated −0.68 with pay, contributed −4.7% of
  composite variance). `build_sow.py` prints the component correlation matrix on every
  run — check it if you add a component back.
- **Q6 allocation**: each CIP's completions are split *equally* across its linked SOCs.
  All 149 VSCS programs and all 1,983 completions match the crosswalk, so nothing is
  dropped, but the equal split is an assumption.
- **VSCS = `[230861, 231165]`** — Community College of Vermont and Vermont State
  University. UVM (231174) is deliberately excluded; it is not part of VSCS.

## Known data traps

- **October 2025 CPS is missing nationally**, so 2025 is an 11-month average.
  `cps_vt_extract.py` divides by the actual month count, not 12.
- **IPUMS CPS is sample microdata** — always weight by `WTFINL`. `COUNT(*)` is meaningless.
- **The CPS rotating panel** means person-months ≠ people. Over 2021–2025 Vermont has
  80,569 person-month records but 16,887 distinct people.
- **The industry export has no 2021 column** — only 2001 and 2025. Sector change over the
  study window is therefore not computed, deliberately, rather than shown from a 2001 base.
- **16 occupations have zero earnings** and are excluded from all wage figures. They
  account for 0.00% of jobs.
- **`bigquery-public-data` and `lightcast.corelmi_us_v3_dat_occ` are expensive.** The
  latter is 3.03 TB, unpartitioned and unclustered — a single filtered probe scans ~735 GB.
  Nothing in this pipeline touches it; if you add county-level demand for RQ7, materialise
  a Vermont slice once rather than querying it live.

## build_compare.py

OEWS wage distributions for Vermont, New Hampshire and the United States, written to
`../data/compare.json`. Vermont and New Hampshire come from the 2025 state file; there
is no 2025 national file in the warehouse, so the US column is OEWS 2024 and every
chart that uses it says so.

Two traps in that source. The national table stores its numerics as strings with
thousands separators, so `SAFE_CAST('96,310' AS FLOAT64)` silently returns NULL and
every US row disappears; commas have to be stripped first. And `#` means "at or above
$239,200" while `*` means suppressed, so both need handling rather than casting.

It also writes `vtLadder`, the mean and five percentiles for each Vermont occupation,
which is what lets the percentile ladder put the mean and the median on one line.

## build_people.py

Person-level earnings from ACS 1-year 2024 (IPUMS USA), written to `../data/people.json`.
Every dot in those charts is one respondent.

Two traps here too. `2024_acs1_household_geographic` holds one row per PERSON, not per
household, so joining on SERIAL alone matches every person in the household and inflates
the sample by household size -- 2.23x. Use `SELECT DISTINCT SERIAL, STATEFIP`. And the
measure is INCEARN, not INCWAGE: wage income alone reads zero for the self-employed,
which would silently drop 135 of Vermont's 2,028 full-time year-round workers.

Columns hold more respondents than a chart can render, so each carries a weighted random
sample drawn without replacement with probability proportional to PERWT. The average and
median lines are computed from every respondent, not from the sampled dots.

## e2e_dots.py, shoot_panels.py

`e2e_dots.py` drives a real browser against `next start` and checks that every tab
renders, that the dot charts draw, that hovering a dot produces a tooltip, that clicking
a column opens the drill-down, and that nothing overflows at 390px. Run it after any
chart change: `next build` compiles a stale identifier happily and it only fails at
runtime. `shoot_panels.py` crops each chart panel to `../_shots/` for eyeballing.
