"""Who advertises in each Vermont county, and in what industry.

The 11/18 review asked for a drill-down on the county map: top 5 employers and
top 5 industries. I filed employers as having no data source, which was wrong --
us_postings carries company_name beside county, and because the table is
clustered on `posted` a two-year Vermont slice dry-runs at under 4 GiB out of a
3.9 TB table.

INDUSTRIES COME FROM THE SAME SCAN. The employment-based version -- which county
actually employs most in each industry -- lives in corelmi_us_v3_dat_ind, which
is neither partitioned nor clustered and costs 486 GiB a run. The NAICS name is
already on every posting, so one more column here answers a NEARBY question for
nothing. It is not the same question, and the app must not pretend it is:

    this is who ADVERTISES, not who EMPLOYS.

A hospital system and a staffing agency look very different on postings than on
payroll, which is the same posting-versus-hiring distinction the Demand tab
already carries. Staffing firms are excluded for that reason, as they are
everywhere else on this dashboard, and the panel says what it is measuring.

The window, the de-duplication and the exclusions match data/demand.json exactly
so the two panels cannot disagree about Vermont's postings.

Dry-runs first and refuses to execute above the ceiling.
"""
import io
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from google.cloud import bigquery

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
CEILING_GIB = 25.0
TOP_N = 5
START, END = "2024-08-01", "2026-07-31"

SQL = f"""
WITH vt AS (
  SELECT county, county_name, company_name, naics_2022_4_name AS industry
  FROM `strada-data-lab-c9d1.lightcast.us_postings`
  WHERE state = '50'
    AND posted BETWEEN '{START}' AND '{END}'
    AND duplicates = 1
    AND NOT COALESCE(company_is_staffing, FALSE)
    AND NOT COALESCE(is_internship, FALSE)
    AND county IS NOT NULL
    -- Explicitly remote roles are dropped. The county on a posting is where the
    -- company filed it, not where the work is, and in Vermont that is not a
    -- small effect: Washington County carries 6,456 remote postings against
    -- Chittenden's 750, which is the whole of its apparent lead over a county
    -- three times its size. National employers register at Montpelier addresses.
    AND COALESCE(remote_type_name, '') != 'Remote'
),
emp AS (
  SELECT county, county_name, company_name AS k, COUNT(*) AS n, 'employer' AS kind
  FROM vt WHERE company_name IS NOT NULL AND company_name != ''
    AND NOT STARTS_WITH(company_name, 'Unclassified')
  GROUP BY 1,2,3
),
ind AS (
  SELECT county, county_name, industry AS k, COUNT(*) AS n, 'industry' AS kind
  FROM vt WHERE industry IS NOT NULL AND industry != ''
    AND NOT STARTS_WITH(industry, 'Unclassified')
  GROUP BY 1,2,3
),
tot AS (SELECT county, COUNT(*) AS postings FROM vt GROUP BY 1)
SELECT r.county, r.county_name, r.kind, r.k, r.n, t.postings
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY county, kind ORDER BY n DESC, k) AS rk
  FROM (SELECT * FROM emp UNION ALL SELECT * FROM ind)
) r
JOIN tot t USING (county)
WHERE r.rk <= {TOP_N}
ORDER BY r.county, r.kind, r.rk
"""

c = bigquery.Client(project="strada-data-lab-c9d1")

dry = c.query(SQL, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
gib = dry.total_bytes_processed / 1024 ** 3
print("dry run: %.2f GiB (ceiling %.0f GiB)" % (gib, CEILING_GIB))
if gib > CEILING_GIB:
    raise SystemExit("refusing to run: %.2f GiB is over the ceiling" % gib)

print("running ...")
df = c.query(SQL).to_dataframe()
print("%d rows over %d counties\n" % (len(df), df["county"].nunique()))

out = {}
for cty, g in df.groupby("county"):
    name = g["county_name"].iloc[0]
    # Lightcast gives "Chittenden, VT", not "Chittenden County, VT"; the rest
    # of the dashboard keys counties on the bare name.
    for suffix in (" County, VT", ", VT", " County"):
        name = name.replace(suffix, "")
    name = name.strip()
    out[cty] = {
        "c": name,
        "postings": int(g["postings"].iloc[0]),
        "employers": [{"n": r.k, "p": int(r.n)}
                      for r in g[g.kind == "employer"].itertuples()],
        "industries": [{"n": r.k, "p": int(r.n)}
                       for r in g[g.kind == "industry"].itertuples()],
    }

for k in sorted(out, key=lambda k: -out[k]["postings"])[:4]:
    v = out[k]
    print("%-12s %6s postings" % (v["c"], "{:,}".format(v["postings"])))
    print("   employers : " + ", ".join("%s (%d)" % (e["n"][:28], e["p"])
                                        for e in v["employers"][:3]))
    print("   industries: " + ", ".join("%s (%d)" % (i["n"][:28], i["p"])
                                        for i in v["industries"][:3]))

PATH = os.path.join(DATA, "county_postings.json")
json.dump({
    "window": "August 2024 – July 2026",
    "measure": "advertised",
    "note": ("Top advertisers and advertised industries per county, from job "
             "postings. This is who ADVERTISES, not who EMPLOYS: a large "
             "employer that rarely posts will not appear, and one that posts "
             "heavily will outrank bigger neighbours. Non-staffing, unique "
             "postings, excluding internships — the same universe as "
             "demand.json. Industry is the posting's own NAICS 4-digit sector. "
             "Explicitly remote roles are excluded and postings Lightcast could "
             "not resolve to a company or an industry are left out of those two "
             "lists: a posting's county is where the employer filed it, not "
             "where the work is, and national employers registered at Vermont "
             "addresses otherwise dominate the county that holds them."),
    "topN": TOP_N,
    "counties": out,
}, io.open(PATH, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
print("\nwrote %s (%s bytes)" % (PATH, "{:,}".format(os.path.getsize(PATH))))
