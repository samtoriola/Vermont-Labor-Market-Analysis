# Workfiles

Every figure the dashboard draws, as a spreadsheet, so the numbers can be checked
without reading the code or running it.

**Start with `00_headline_figures.csv`.** It lists each number quoted in a caption,
a read-out or a tile, with the file and the arithmetic that reproduces it.

These are a build output. `scripts/build_workfiles.py` writes them from the same
committed JSON in `data/` that the app imports at build time, so a figure here and
the same figure on screen come from one source and cannot drift. Re-run it after
any data refresh:

```
python scripts/build_workfiles.py
```

Nothing in the app reads these files.

## The files

| File | What it carries | Rows |
| --- | --- | --- |
| `00_headline_figures.csv` | Every number quoted in a caption, a read-out or a tile, with the workfile and the arithmetic that reproduces it | 12 rows |
| `01_occupations_master.csv` | Every Vermont occupation | 796 rows |
| `02_overview_and_wage_by_group.csv` | The Overview chart and Wage quality / Wage benchmark, by occupation group | 22 rows |
| `03_pathways_credential_ladder.csv` | Pathways / By credential level | 5 rows |
| `04_pathways_openings_by_credential.csv` | Pathways / Which credentials pay | 5 rows |
| `05_wage_county_floor.csv` | Wage quality / County living wage | 14 rows |
| `06_employment_sectors.csv` | Employment / Industry sectors | 21 rows |
| `07_employment_occupation_groups.csv` | Employment / Occupation | 22 rows |
| `08_opportunity_scores.csv` | Opportunities / Highest scoring | 30 rows |
| `09_vscs_alignment_by_group.csv` | VSCS alignment / Against demand | 22 rows |
| `10_vscs_production.csv` | VSCS alignment / Production by award | 10 rows |
| `11_regions_counties.csv` | Regions / Counties compared | 15 rows |
| `12_demand_what_postings_ask.csv` | Demand & growth / General demand | 18 rows |
| `13_regions_county_map.csv` | Regions / County map | 14 rows |

## How to check a figure by hand

Each file carries the inputs and the intermediate steps, not just the answer, so
a measure can be redone with a calculator.

**"41% of priced jobs pay below a living wage"** — open
`01_occupations_master.csv`. For one occupation, `pct_of_jobs_below_benchmark` is
where $49816 falls along its own `p10`&ndash;`p90` ladder, interpolated straight-line
between the two published percentiles either side of it, and clamped at 0 and 100
outside them. `jobs_below_benchmark` is that share times `jobs_2025`. Sum both
columns and divide: that is the Overview headline, and `02` has the same sum per
occupation group.

**A credential rung's pay range** — `03_pathways_credential_ladder.csv` carries
`pooled_*` and `published_*` side by side. The pooled one is what the chart draws:
the value V at which a given share of the rung's jobs pay less than V, built from
its occupations' ladders weighted by employment. The published one is the mean of
those occupations' percentiles, which is a different statistic and understates the
spread by up to 44%. If a figure on screen matches the published column rather
than the pooled one, something has regressed.

**VSCS alignment** — `09_vscs_alignment_by_group.csv` carries both denominators.
The chart divides by `openings_asking_for_a_vscs_credential`; `pct_of_all_openings`
is the measure that replaced and is kept for comparison.

## What these cannot settle

Three things are modelled rather than observed, and no amount of checking the
arithmetic will change that:

- **Graduates attributed to an occupation.** CIP-to-SOC is many-to-many, so each
  program's completions are split across the occupations it feeds in proportion to
  their Vermont employment. 32.5% of completions move under that assumption. It
  is a model of where graduates go, not a record of where they went, and
  1,700 of 1,983 completions land in a Vermont occupation at all.
- **Projected growth to 2030.** A Lightcast model, not an observation. Change over
  2021&ndash;2025 is what happened; the two are kept in separate columns for that
  reason.
- **The openings divisor.** `openings_per_year` is Lightcast's 2021&ndash;2025
  openings divided by 4. If that window is meant inclusively as five years, every
  openings figure here scales down by a fifth.

Measure definitions, suppression rules and the full caveat list are on the
dashboard's Methods tab.
