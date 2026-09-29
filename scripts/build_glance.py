"""Vermont labour-force structure for the overview panel, CPS 2025.

One source, one vintage, so nothing on this panel mixes surveys. Earnings are not
here: they live on the wage tab, where the ACS universe is stated in full.

Two things this script settles rather than assumes:

Full-time is derived from UHRSWORKT (usual hours, 35+), not WKSTAT, whose level codes
are easy to misread. 690 of 6,976 employed records report 997, "hours vary", and cannot
be classified either way, so the full-time share is expressed over workers with
reportable hours and the unclassified group is reported alongside rather than silently
folded into one side.

The unemployment rate carries an interval. CPS re-interviews the same households on a
4-8-4 rotation, so 7,166 person-month records in the 2025 Vermont labour force come
from only 2,726 distinct people. The interval uses the distinct-person count, which
widens it from +/-0.38pp to +/-0.62pp -- the honest figure. Note also that Vermont's
official rate comes from LAUS, which is model-based; this is the direct CPS estimate
and the two differ by construction.
"""
import json, os, pathlib
import numpy as np
import warnings
from google.cloud import bigquery

warnings.filterwarnings("ignore")
c = bigquery.Client(project="strada-data-lab-c9d1")
HERE = pathlib.Path(__file__).resolve().parent

YEAR = 2025
HOURS_VARY = 997
FT_HOURS = 35

# WTFINL sums across every month in the year, so divide by the month count to get a
# monthly average. October 2025 is missing nationally, hence 11 rather than 12.
SQL = f"""
SELECT
  COUNT(DISTINCT MONTH) AS months,
  COUNTIF(LABFORCE = 2) AS rec_lf,
  COUNT(DISTINCT IF(LABFORCE = 2, CPSIDP, NULL)) AS ppl_lf,
  COUNTIF(EMPSTAT IN (10, 12)) AS rec_emp,
  COUNTIF(EMPSTAT IN (21, 22)) AS rec_unemp,
  SUM(WTFINL) AS pop16,
  SUM(IF(LABFORCE = 2, WTFINL, 0)) AS lf,
  SUM(IF(EMPSTAT IN (10, 12), WTFINL, 0)) AS emp,
  SUM(IF(EMPSTAT IN (21, 22), WTFINL, 0)) AS unemp,
  SUM(IF(EMPSTAT IN (10, 12) AND UHRSWORKT >= {FT_HOURS}
         AND UHRSWORKT < {HOURS_VARY}, WTFINL, 0)) AS ft,
  SUM(IF(EMPSTAT IN (10, 12) AND UHRSWORKT < {FT_HOURS}, WTFINL, 0)) AS pt,
  SUM(IF(EMPSTAT IN (10, 12) AND UHRSWORKT = {HOURS_VARY}, WTFINL, 0)) AS vary,
  COUNTIF(EMPSTAT IN (10, 12) AND UHRSWORKT >= {FT_HOURS}
          AND UHRSWORKT < {HOURS_VARY}) AS rec_ft,
  COUNTIF(EMPSTAT IN (10, 12) AND UHRSWORKT < {FT_HOURS}) AS rec_pt,
  COUNTIF(EMPSTAT IN (10, 12) AND UHRSWORKT = {HOURS_VARY}) AS rec_vary
FROM `strada-data-lab-c9d1.monthly_cps.cps`
WHERE STATEFIP = 50 AND YEAR = {YEAR} AND AGE >= 16
"""

r = c.query(SQL).to_dataframe().iloc[0]
m = int(r.months)
mo = lambda v: float(v) / m  # noqa: E731 -- monthly average from the summed weights

pop16, lf, emp, unemp = mo(r.pop16), mo(r.lf), mo(r.emp), mo(r.unemp)
ft, pt, vary = mo(r.ft), mo(r.pt), mo(r.vary)

ur = unemp / lf
lfpr = lf / pop16
determinate = ft + pt
ft_share = ft / determinate
vary_share = vary / emp

# Interval on the rate, using distinct people rather than person-month records.
n_eff = int(r.ppl_lf)
se = float(np.sqrt(ur * (1 - ur) / n_eff))
ci = 1.96 * se

print(f"Vermont CPS {YEAR}, {m}-month average")
print(f"  population 16+           {pop16:>10,.0f}")
print(f"  labour force             {lf:>10,.0f}   LFPR {lfpr*100:5.1f}%")
print(f"  employed                 {emp:>10,.0f}")
print(f"  unemployed               {unemp:>10,.0f}   rate {ur*100:5.2f}% "
      f"+/-{ci*100:.2f}pp  [{(ur-ci)*100:.2f}%, {(ur+ci)*100:.2f}%]")
print(f"    records: {int(r.rec_unemp)} unemployed person-months, "
      f"{int(r.rec_lf)} in the labour force, {n_eff} distinct people")
print(f"  full-time (35+ hrs)      {ft:>10,.0f}   {ft_share*100:5.1f}% "
      f"of workers with reportable hours (n={int(r.rec_ft)})")
print(f"  part-time (<35 hrs)      {pt:>10,.0f}   {(1-ft_share)*100:5.1f}% "
      f"(n={int(r.rec_pt)})")
print(f"  hours vary, unclassified {vary:>10,.0f}   {vary_share*100:5.1f}% "
      f"of the employed (n={int(r.rec_vary)})")

out = {
    "year": YEAR,
    "months": m,
    "pop16": round(pop16),
    "lf": round(lf),
    "emp": round(emp),
    "unemp": round(unemp),
    "lfpr": round(lfpr * 1000) / 10,
    "ur": round(ur * 10000) / 100,
    "urCi": round(ci * 10000) / 100,
    "ft": round(ft),
    "pt": round(pt),
    "vary": round(vary),
    "ftShare": round(ft_share * 1000) / 10,
    "ptShare": round((1 - ft_share) * 1000) / 10,
    "varyShare": round(vary_share * 1000) / 10,
    "nUnemp": int(r.rec_unemp),
    "nLf": int(r.rec_lf),
    "nPeopleLf": n_eff,
}

p = HERE.parent / "data" / "glance.json"
p.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(f"\nwrote {p} ({os.path.getsize(p):,} bytes)")
