"""Materialises the Vermont slice of Lightcast job postings. Run once.

Feeds the General demand panel: what employers ask for at the door, in
education, experience and skills, for Vermont against its counties, a
neighbouring state and the country.

WHY A SEPARATE PULL AND NOT THE EXISTING POSTINGS EXPORT
--------------------------------------------------------
The Drive folder already holds Job_Postings_Table_Vermont_*.csv, but like every
other Lightcast export there it is statewide and carries no education,
experience or skill breakdown. `us_postings` carries all three on the row, plus
`county_name`, which is also what makes a county comparison possible at all.

COST
----
`us_postings` is 3,684 GB but unpartitioned, so the scan is the sum of the
columns referenced and nothing else -- never SELECT `body`, which is almost all
of that size. The two queries here are a few GiB each.

METHOD, MATCHED TO THE REFERENCE VIEW
-------------------------------------
Postings are filtered the way the published comparison this panel is modelled on
filters them: unique, non-staffing, excluding internships, permanent positions.
`min_edulevels_name` is never NULL -- postings that say nothing carry the
literal 'No Education Listed', so the denominator for "of postings that specify"
is the total minus that bucket. Roughly half of Vermont postings say nothing,
which is a fact about what employers write down, not about what they require,
and the panel has to say so.

Skills are posting share only. The reference view colours each skill by whether
it is in deficit or surplus against the local candidate pool, which needs
Lightcast profiles; profiles skew college-educated, white-collar and urban, and
in a rural state that is a distortion rather than a caveat. Posting share on its
own is a claim the data can carry.
"""
import os
import sys

from google.cloud import bigquery

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FOLDER = r"G:\My Drive\Vermont Labor Market Analysis"
OUT_REQ = os.path.join(FOLDER, "VT_Postings_Education_Experience_by_Area.csv")
OUT_SKILL = os.path.join(FOLDER, "VT_Postings_Skills_by_Area.csv")

MAX_SCAN_GIB = 60
PRICE_PER_TIB = 6.25

PROJECT = "strada-data-lab-c9d1"
P = f"`{PROJECT}.lightcast.us_postings`"

# Two years, the window the panel reports.
WINDOW = ("2024-08-01", "2026-07-31")
FILTERS = f"""
  posted BETWEEN '{WINDOW[0]}' AND '{WINDOW[1]}'
  AND NOT IFNULL(is_internship, false)
  AND NOT IFNULL(company_is_staffing, false)
"""

# Vermont by county, plus the two benchmarks the dashboard already uses. New
# Hampshire is the comparator on the pay charts; keeping it here means the two
# halves of the dashboard compare Vermont with the same places.
AREAS = f"""
  SELECT 'United States' AS area, 'NATION' AS area_type, {{cols}} FROM {P} WHERE {{f}}
  UNION ALL
  SELECT 'Vermont', 'STATE', {{cols}} FROM {P} WHERE {{f}} AND state_name = 'Vermont'
  UNION ALL
  SELECT 'New Hampshire', 'STATE', {{cols}} FROM {P} WHERE {{f}} AND state_name = 'New Hampshire'
  UNION ALL
  SELECT county_name, 'COUNTY', {{cols}} FROM {P} WHERE {{f}} AND state_name = 'Vermont'
"""

# One row per area x education x experience band. Marginalising either way
# downstream is free, and it costs the same single scan as asking for one.
BANDS = """CASE
      WHEN min_years_experience IS NULL THEN 'Not stated'
      WHEN min_years_experience <= 1 THEN '0 - 1 years'
      WHEN min_years_experience <= 3 THEN '2 - 3 years'
      WHEN min_years_experience <= 6 THEN '4 - 6 years'
      WHEN min_years_experience <= 9 THEN '7 - 9 years'
      ELSE '10+ years' END"""

SQL_REQ = f"""
WITH a AS (
{AREAS.format(cols="min_edulevels_name AS education, " + BANDS + " AS experience", f=FILTERS)}
)
SELECT area, area_type, IFNULL(education, 'No Education Listed') AS education,
       experience, COUNT(*) AS postings
FROM a
GROUP BY 1, 2, 3, 4
ORDER BY area, education, experience
"""

# Skills are three separate named lists on the row rather than one typed column,
# so the type is made explicit here instead of being inferred later.
SKILL_COLS = """
  'Common' AS skill_type, s AS skill FROM {p}, UNNEST(JSON_VALUE_ARRAY(common_skills_name)) s WHERE {f}
"""


def skills_sql():
    parts = []
    for label, col in (("Common", "common_skills_name"),
                       ("Specialized", "specialized_skills_name"),
                       ("Software", "software_skills_name")):
        for area, atype, extra in (("'United States'", "'NATION'", ""),
                                   ("'Vermont'", "'STATE'", " AND state_name = 'Vermont'"),
                                   ("'New Hampshire'", "'STATE'",
                                    " AND state_name = 'New Hampshire'"),
                                   ("county_name", "'COUNTY'", " AND state_name = 'Vermont'")):
            parts.append(
                f"SELECT {area} AS area, {atype} AS area_type, '{label}' AS skill_type, "
                f"s AS skill FROM {P}, UNNEST(JSON_VALUE_ARRAY({col})) s "
                f"WHERE {FILTERS} {extra}"
            )
    body = "\n  UNION ALL\n  ".join(parts)
    # A skill named on fewer than 0.5% of an area's postings is noise in a
    # ranking, which is the same floor the reference view applies.
    return f"""
WITH a AS (
  {body}
),
n AS (SELECT area, skill_type, COUNT(*) AS marks FROM a GROUP BY 1, 2)
SELECT a.area, a.area_type, a.skill_type, a.skill, COUNT(*) AS postings
FROM a JOIN n USING (area, skill_type)
GROUP BY 1, 2, 3, 4
HAVING COUNT(*) >= 50
ORDER BY area, skill_type, postings DESC
"""


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
        print("  REFUSED TO WRITE: query returned no rows.")
        return None, budget - billed

    df.to_csv(out, index=False)
    print("  wrote %s" % out)
    print("    rows %s | bytes %s | areas %d"
          % (f"{len(df):,}", f"{os.path.getsize(out):,}", df["area"].nunique()))
    return df, budget - billed


def main():
    if not os.path.isdir(FOLDER):
        print("REFUSED: %s is not reachable -- is the Drive mounted?" % FOLDER)
        return 1

    client = bigquery.Client(project=PROJECT)
    budget = MAX_SCAN_GIB

    req, budget = run(client, "education and experience", SQL_REQ, OUT_REQ, budget)
    if req is not None:
        vt = req[req.area == "Vermont"]
        tot = vt.postings.sum()
        stated = vt[vt.education != "No Education Listed"].postings.sum()
        print("    Vermont: %s postings, %s state an education level (%.0f%%)"
              % (f"{tot:,}", f"{stated:,}", stated / tot * 100))

    skl, budget = run(client, "skills", skills_sql(), OUT_SKILL, budget)
    if skl is not None:
        print("    skills per type: %s"
              % skl[skl.area == "Vermont"].groupby("skill_type").skill.nunique().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
