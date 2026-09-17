from google.cloud import bigquery
import warnings
warnings.filterwarnings("ignore")
c = bigquery.Client(project="strada-data-lab-c9d1")

sql = """
SELECT county_fips_code, county_name, ST_ASGEOJSON(county_geom) AS gj
FROM `bigquery-public-data.geo_us_boundaries.counties`
WHERE state_fips_code = '50'
ORDER BY county_fips_code
"""
try:
    dry = c.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True))
    print("dry-run OK: %.4f GB" % (dry.total_bytes_processed / 1e9))
    df = c.query(sql).to_dataframe()
    print("rows:", len(df))
    print(df[["county_fips_code", "county_name"]].to_string(index=False))
    print("\ngeojson size per county (chars):")
    print(df["gj"].str.len().describe().to_string())
    df.to_json("vt_counties_raw.json", orient="records")
    print("\nwrote vt_counties_raw.json")
except Exception as e:
    print("FAILED:", type(e).__name__, str(e)[:400])
