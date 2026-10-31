"""Materialises the Vermont county slice of Lightcast Core LMI. Run once.

Closes the half of SOW research question 7 that has been open since the start:
regional attainment and wage sufficiency are already in sow.json from ACS, but
occupational demand and wage premiums by region are not, because every Lightcast
CSV export in the Drive folder is statewide. Core LMI carries all 14 counties.

WHICH TABLE, AND WHY NOT THE OBVIOUS ONE
----------------------------------------
The obvious source is `corelmi_us_v3_dat_occ`. It is 2,820 GiB, unpartitioned
and unclustered, and a WHERE clause removes no bytes from an unpartitioned scan
-- the cost is the sum of the columns referenced, whatever the filter. Asking it
for employment costs 643 GiB; asking for employment and average earnings, 727.

`corelmi_us_v3_dat_occ_earn` is 67.6 GiB, shares the grain exactly
(year x area x occid x class), and carries `emp` *and* the whole percentile set
p10/p25/p50/p75/p90 that `dat_occ` does not have at all. It is both the cheaper
table and the better one: the dashboard compares pay against a living wage, and
that is a percentile question, not an average question.

`corelmi_us_v3_dat_occ_hires_seps` (52.2 GiB) adds hiring and separations by
county, which is the demand half of RQ7.

CLASS -- AND WHICH CLASSES THE REST OF THE DASHBOARD IS ON
----------------------------------------------------------
`classid` in these fact tables takes only the values 1-4: QCEW employees,
non-QCEW employees, self-employed, extended proprietors. There is no class 0
row. "All Employment" (classid 0) exists only in `dim_classid`, as the level-1
parent of those four. Filtering the facts to classid = '0' returns nothing at
all -- silently, and after a full scan.

Which classes to keep is not a free choice, because the figures already on the
dashboard came from a Lightcast CSV export on one particular basis. Measured:

    QCEW employees                308,224
    + non-QCEW employees          326,610     <- the export's basis
    + self-employed               359,899
    + extended proprietors        458,172

The dashboard's statewide total is 326,582. Classes 1+2 reproduce it to within
28 jobs (0.009%), so **classes 1 and 2 are the basis to use** for anything that
has to sit beside an existing figure. Summing all four would put a county total
40% above the state total shown on every other tab.

All four classes are kept in the CSV so that choice stays visible and reversible
downstream, rather than being baked in here where nobody would see it.

EARNINGS ARE HOURLY
-------------------
`earn_p10..p90` are hourly rates (Vermont 2025 detailed median: $28.76), not the
annual figures the rest of the dashboard shows. Multiply by LC.hours (2080), the
same constant the living-wage benchmark already uses.

OCCUPATION LEVELS
-----------------
`dat_occ_earn` carries only level 1 ("Total, All Occupations") and level 5
(detailed SOC, 798 of them here) -- not the level-2 major groups the reference
docs describe for `dim_occid`. The 22 occupation groups have to be rolled up
from detailed SOC with the SOC_MAJOR map in build_maps.py, exactly as build.py
already does for the statewide export.

COST GUARD
----------
Billed against a shared account whose monthly free-tier headroom this account
cannot read (`bigquery.jobs.listAll` denied), so the script dry-runs first,
prints the estimate, and refuses above MAX_SCAN_GIB rather than assuming the
tier is open.
"""
import os
import sys

from google.cloud import bigquery

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
OUT_EARN = os.path.join(FOLDER, "VT_CoreLMI_Occupation_by_County_2021_2025.csv")
OUT_FLOW = os.path.join(FOLDER, "VT_CoreLMI_HiresSeps_by_County_2021_2025.csv")

# Deliberately well under the 1 TiB monthly free tier, because this is not the
# only thing drawing on it.
MAX_SCAN_GIB = 120
PRICE_PER_TIB = 6.25

PROJECT = "strada-data-lab-c9d1"
EARN = f"`{PROJECT}.lightcast.corelmi_us_v3_dat_occ_earn`"
FLOW = f"`{PROJECT}.lightcast.corelmi_us_v3_dat_occ_hires_seps`"
DIM_OCC = f"`{PROJECT}.lightcast.corelmi_us_v3_dim_occid`"

# The 14 counties, plus the state and the nation as the benchmarks the rest of
# the dashboard already compares against. 50999 is Lightcast's "county not
# reported" bucket, kept so the counties can be shown to add up to the state
# rather than silently falling short of it.
COUNTIES = [str(50000 + i) for i in range(1, 28, 2)]
AREAS = ["0", "50", "50999"] + COUNTIES
AREA_LIST = ", ".join(repr(a) for a in AREAS)
# Observed: the latest year and the four before it. Outlook: 2030, five years
# ahead, which is the horizon every projection on the dashboard already uses.
#
# Note what the filter does and does not buy. The table is unpartitioned, so
# narrowing the years removes no bytes from the scan and saves nothing on cost;
# it only keeps the CSV small enough to open. Widening it later costs another
# full scan, so ask for everything you might want in one go.
#
# Neither of the two tables here actually reaches 2030: dat_occ_earn stops at
# 2025 and dat_occ_hires_seps at 2027. The clause is correct and harmless, and
# it will pick 2030 up if Lightcast extends them. County-level projections to
# 2030 live in `dat_occ`, which is the 643+ GiB table this script exists to
# avoid -- see the note in scripts/README.md before reaching for it.
YEARS = "(year BETWEEN 2021 AND 2025 OR year = 2030)"

# occid_name and areaid_name are carried on these tables, but they are wide
# strings repeated across billions of rows; the dimension join costs nothing by
# comparison and says the same thing.
SQL_EARN = f"""
WITH v AS (
  SELECT year, classid, areaid, occid, emp,
         earn_avg, earn_p10, earn_p25, earn_p50, earn_p75, earn_p90
  FROM {EARN}
  WHERE {YEARS} AND areaid IN ({AREA_LIST})
),
o AS (SELECT DISTINCT occid, name AS occupation, level AS occ_level FROM {DIM_OCC})
SELECT v.areaid, v.occid, o.occupation, o.occ_level, v.year, v.classid,
       v.emp, v.earn_avg, v.earn_p10, v.earn_p25, v.earn_p50, v.earn_p75, v.earn_p90
FROM v JOIN o USING (occid)
ORDER BY v.areaid, o.occ_level, v.occid, v.year, v.classid
"""

SQL_FLOW = f"""
WITH v AS (
  SELECT year, classid, areaid, occid, hires, seps
  FROM {FLOW}
  WHERE {YEARS} AND areaid IN ({AREA_LIST})
),
o AS (SELECT DISTINCT occid, name AS occupation, level AS occ_level FROM {DIM_OCC})
SELECT v.areaid, v.occid, o.occupation, o.occ_level, v.year, v.classid, v.hires, v.seps
FROM v JOIN o USING (occid)
ORDER BY v.areaid, o.occ_level, v.occid, v.year, v.classid
"""

JOBS = [("occupation employment and earnings", SQL_EARN, OUT_EARN),
        ("hires and separations", SQL_FLOW, OUT_FLOW)]


def run(client, label, sql, out, budget):
    dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    gib = dry.total_bytes_processed / 2**30
    print("\n%s" % label)
    print("  estimated scan: %.1f GiB  (~$%.2f at full rate)" % (gib, gib / 1024 * PRICE_PER_TIB))
    if gib > budget:
        print("  REFUSED: over the %.0f GiB left in this run's budget." % budget)
        return None, budget

    job = client.query(sql)
    df = job.to_dataframe()
    billed = job.total_bytes_billed / 2**30
    print("  billed: %.1f GiB" % billed)

    if df.empty:
        # The classid trap above cost a 759 GiB scan that returned nothing, so an
        # empty result is now treated as a failure rather than written out.
        print("  REFUSED TO WRITE: query returned no rows. Check the filters.")
        return None, budget - billed

    df.to_csv(out, index=False)
    print("  wrote %s" % out)
    print("    rows %s | bytes %s | areas %d | years %s"
          % (f"{len(df):,}", f"{os.path.getsize(out):,}",
             df["areaid"].nunique(), sorted(df["year"].unique())))
    return df, budget - billed


def main():
    if not os.path.isdir(FOLDER):
        print("REFUSED: %s is not reachable -- is the Drive mounted?" % FOLDER)
        return 1

    client = bigquery.Client(project=PROJECT)
    budget = MAX_SCAN_GIB
    out = {}
    for label, sql, path in JOBS:
        df, budget = run(client, label, sql, path, budget)
        out[label] = df

    df = out.get("occupation employment and earnings")
    if df is not None:
        # The slice is only usable if the counties reconstruct the state.
        # Lightcast reports them independently, so this is a check, not an
        # identity, and the gap is worth printing either way.
        print("\ncounties against the state, all classes, major groups only:")
        d = df[df.occ_level == 2]
        for y in (2021, 2025, 2030):
            dy = d[d.year == y]
            st = dy[dy.areaid == "50"]["emp"].sum()
            ct = dy[~dy.areaid.isin(["50", "0"])]["emp"].sum()
            if st:
                print("  %d: counties %s vs state %s (%+.2f%%)"
                      % (y, f"{ct:,.0f}", f"{st:,.0f}", (ct / st - 1) * 100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
