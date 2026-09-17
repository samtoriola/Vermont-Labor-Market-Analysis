"""Vermont CPS 2021-2025 extract for the labor market dashboard.

Weighting: WTFINL. Annual-average employment = SUM(WTFINL)/n_months, since each
monthly sample carries a full population weight. Oct 2025 is missing nationally,
so the 2021-2025 window has 59 months, not 60.
"""
from google.cloud import bigquery
import warnings, json
warnings.filterwarnings("ignore")
c = bigquery.Client(project="strada-data-lab-c9d1")

OCC_FAMILY = """
CASE
 WHEN OCC BETWEEN   10 AND  440 THEN 'Management'
 WHEN OCC BETWEEN  500 AND  960 THEN 'Business & Financial Operations'
 WHEN OCC BETWEEN 1005 AND 1240 THEN 'Computer & Mathematical'
 WHEN OCC BETWEEN 1300 AND 1560 THEN 'Architecture & Engineering'
 WHEN OCC BETWEEN 1600 AND 1980 THEN 'Life, Physical & Social Science'
 WHEN OCC BETWEEN 2001 AND 2060 THEN 'Community & Social Service'
 WHEN OCC BETWEEN 2100 AND 2180 THEN 'Legal'
 WHEN OCC BETWEEN 2205 AND 2555 THEN 'Educational Instruction & Library'
 WHEN OCC BETWEEN 2600 AND 2920 THEN 'Arts, Design, Entertainment & Media'
 WHEN OCC BETWEEN 3000 AND 3550 THEN 'Healthcare Practitioners & Technical'
 WHEN OCC BETWEEN 3601 AND 3655 THEN 'Healthcare Support'
 WHEN OCC BETWEEN 3700 AND 3960 THEN 'Protective Service'
 WHEN OCC BETWEEN 4000 AND 4160 THEN 'Food Preparation & Serving'
 WHEN OCC BETWEEN 4200 AND 4255 THEN 'Building & Grounds Cleaning'
 WHEN OCC BETWEEN 4330 AND 4655 THEN 'Personal Care & Service'
 WHEN OCC BETWEEN 4700 AND 4965 THEN 'Sales'
 WHEN OCC BETWEEN 5000 AND 5940 THEN 'Office & Administrative Support'
 WHEN OCC BETWEEN 6005 AND 6130 THEN 'Farming, Fishing & Forestry'
 WHEN OCC BETWEEN 6200 AND 6950 THEN 'Construction & Extraction'
 WHEN OCC BETWEEN 7000 AND 7640 THEN 'Installation, Maintenance & Repair'
 WHEN OCC BETWEEN 7700 AND 8990 THEN 'Production'
 WHEN OCC BETWEEN 9005 AND 9760 THEN 'Transportation & Material Moving'
 WHEN OCC BETWEEN 9800 AND 9920 THEN 'Military'
 ELSE 'Unclassified' END
"""

IND_SECTOR = """
CASE
 WHEN IND BETWEEN  170 AND  290 THEN 'Agriculture, Forestry, Fishing & Hunting'
 WHEN IND BETWEEN  370 AND  490 THEN 'Mining, Quarrying, Oil & Gas'
 WHEN IND BETWEEN  570 AND  690 THEN 'Utilities'
 WHEN IND = 770                 THEN 'Construction'
 WHEN IND BETWEEN 1070 AND 3990 THEN 'Manufacturing'
 WHEN IND BETWEEN 4070 AND 4590 THEN 'Wholesale Trade'
 WHEN IND BETWEEN 4670 AND 5790 THEN 'Retail Trade'
 WHEN IND BETWEEN 6070 AND 6390 THEN 'Transportation & Warehousing'
 WHEN IND BETWEEN 6470 AND 6780 THEN 'Information'
 WHEN IND BETWEEN 6870 AND 6992 THEN 'Finance & Insurance'
 WHEN IND BETWEEN 7071 AND 7190 THEN 'Real Estate & Rental'
 WHEN IND BETWEEN 7270 AND 7490 THEN 'Professional, Scientific & Technical'
 WHEN IND BETWEEN 7570 AND 7580 THEN 'Management of Companies'
 WHEN IND BETWEEN 7590 AND 7790 THEN 'Administrative, Support & Waste Mgmt'
 WHEN IND BETWEEN 7860 AND 7890 THEN 'Educational Services'
 WHEN IND BETWEEN 7970 AND 8470 THEN 'Health Care & Social Assistance'
 WHEN IND BETWEEN 8561 AND 8590 THEN 'Arts, Entertainment & Recreation'
 WHEN IND BETWEEN 8660 AND 8690 THEN 'Accommodation & Food Services'
 WHEN IND BETWEEN 8770 AND 9290 THEN 'Other Services'
 WHEN IND BETWEEN 9370 AND 9590 THEN 'Public Administration'
 WHEN IND BETWEEN 9670 AND 9870 THEN 'Military'
 ELSE 'Unclassified' END
"""

# IPUMS CPS EDUC -> pathway buckets
EDUC_PATH = """
CASE
 WHEN EDUC < 73             THEN 'Less than high school'
 WHEN EDUC = 73             THEN 'High school diploma'
 WHEN EDUC IN (81)          THEN 'Some college, no degree'
 WHEN EDUC IN (91,92)       THEN 'Associate degree (sub-baccalaureate)'
 WHEN EDUC = 111            THEN "Bachelor's degree"
 WHEN EDUC IN (123,124,125) THEN 'Graduate or professional degree'
 ELSE 'Unknown' END
"""

EMPLOYED = "EMPSTAT IN (10,12)"
BASE = "STATEFIP = 50 AND YEAR BETWEEN 2021 AND 2025 AND AGE >= 16 AND WTFINL > 0"

out = {}

# months in window (for annual-average scaling)
nm = c.query(f"""SELECT COUNT(DISTINCT CONCAT(CAST(YEAR AS STRING),'-',CAST(MONTH AS STRING))) m
FROM `strada-data-lab-c9d1.monthly_cps.cps` WHERE {BASE}""").to_dataframe().m.iloc[0]
out["n_months"] = int(nm)
print("months in window:", nm)

# 1. occupational family
q1 = f"""
SELECT {OCC_FAMILY} AS family,
       COUNT(*) AS n_unweighted,
       COUNT(DISTINCT IF(CPSIDP>0,CPSIDP,NULL)) AS uniq_persons,
       SUM(WTFINL)/{nm} AS avg_employment
FROM `strada-data-lab-c9d1.monthly_cps.cps`
WHERE {BASE} AND {EMPLOYED}
GROUP BY 1 ORDER BY avg_employment DESC
"""
out["by_family"] = c.query(q1).to_dataframe().to_dict("records")

# 2. family x industry
q2 = f"""
SELECT {OCC_FAMILY} AS family, {IND_SECTOR} AS sector,
       COUNT(*) AS n_unweighted, SUM(WTFINL)/{nm} AS avg_employment
FROM `strada-data-lab-c9d1.monthly_cps.cps`
WHERE {BASE} AND {EMPLOYED}
GROUP BY 1,2 HAVING n_unweighted > 0 ORDER BY avg_employment DESC
"""
out["family_x_sector"] = c.query(q2).to_dataframe().to_dict("records")

# 3. family x educational attainment of incumbents
q3 = f"""
SELECT {OCC_FAMILY} AS family, {EDUC_PATH} AS pathway,
       COUNT(*) AS n_unweighted, SUM(WTFINL)/{nm} AS avg_employment
FROM `strada-data-lab-c9d1.monthly_cps.cps`
WHERE {BASE} AND {EMPLOYED}
GROUP BY 1,2 ORDER BY 1,2
"""
out["family_x_education"] = c.query(q3).to_dataframe().to_dict("records")

# 4. industry sector totals
q4 = f"""
SELECT {IND_SECTOR} AS sector, COUNT(*) AS n_unweighted,
       SUM(WTFINL)/{nm} AS avg_employment
FROM `strada-data-lab-c9d1.monthly_cps.cps`
WHERE {BASE} AND {EMPLOYED}
GROUP BY 1 ORDER BY avg_employment DESC
"""
out["by_sector"] = c.query(q4).to_dataframe().to_dict("records")

# 5. statewide education pathway shares (all employed)
q5 = f"""
SELECT {EDUC_PATH} AS pathway, COUNT(*) AS n_unweighted,
       SUM(WTFINL)/{nm} AS avg_employment
FROM `strada-data-lab-c9d1.monthly_cps.cps`
WHERE {BASE} AND {EMPLOYED}
GROUP BY 1 ORDER BY avg_employment DESC
"""
out["by_pathway"] = c.query(q5).to_dataframe().to_dict("records")

# 6. annual trend: employment, LF, unemployment rate, BA+ share
q6 = f"""
SELECT YEAR,
  COUNT(DISTINCT MONTH) months,
  SUM(IF({EMPLOYED}, WTFINL, 0))/COUNT(DISTINCT MONTH) AS employment,
  SUM(IF(LABFORCE=2, WTFINL, 0))/COUNT(DISTINCT MONTH) AS labor_force,
  SUM(IF(EMPSTAT IN (20,21,22), WTFINL,0)) / NULLIF(SUM(IF(LABFORCE=2,WTFINL,0)),0) AS unemp_rate,
  SUM(IF(AGE>=25 AND EDUC>=111, WTFINL,0)) / NULLIF(SUM(IF(AGE>=25,WTFINL,0)),0) AS ba_plus_share_25p
FROM `strada-data-lab-c9d1.monthly_cps.cps`
WHERE {BASE}
GROUP BY 1 ORDER BY 1
"""
out["annual_trend"] = c.query(q6).to_dataframe().to_dict("records")

# 7. family trend 2021 vs 2025 (CPS-observed change in employment base)
q7 = f"""
SELECT {OCC_FAMILY} AS family, YEAR,
       COUNT(*) n_unweighted,
       SUM(WTFINL)/COUNT(DISTINCT MONTH) AS avg_employment
FROM `strada-data-lab-c9d1.monthly_cps.cps`
WHERE {BASE} AND {EMPLOYED} AND YEAR IN (2021,2025)
GROUP BY 1,2 ORDER BY 1,2
"""
out["family_trend"] = c.query(q7).to_dataframe().to_dict("records")

with open("cps_vt_dashboard_data.json","w") as f:
    json.dump(out, f, indent=1, default=float)

print("\n=== occupational families (annual avg employment, VT 2021-2025) ===")
for r in out["by_family"]:
    print(f"  {r['family']:38s} {r['avg_employment']:>9,.0f}  n={r['n_unweighted']:>5d} uniq={r['uniq_persons']:>4d}")
print("\n=== pathway shares ===")
tot = sum(r["avg_employment"] for r in out["by_pathway"])
for r in out["by_pathway"]:
    print(f"  {r['pathway']:38s} {r['avg_employment']:>9,.0f}  {r['avg_employment']/tot*100:5.1f}%  n={r['n_unweighted']}")
print("\n=== annual trend ===")
for r in out["annual_trend"]:
    print(f"  {int(r['YEAR'])} m={int(r['months'])} emp={r['employment']:>9,.0f} "
          f"unemp={r['unemp_rate']*100:4.1f}% BA+={r['ba_plus_share_25p']*100:4.1f}%")
print("\nwrote cps_vt_dashboard_data.json")
