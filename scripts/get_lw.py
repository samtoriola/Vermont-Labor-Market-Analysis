from google.cloud import bigquery
import warnings
warnings.filterwarnings("ignore")
c = bigquery.Client(project="strada-data-lab-c9d1")

print(c.query("""
SELECT region_type, COUNT(*) n, MIN(region_id) mn, MAX(region_id) mx
FROM `strada-data-lab-c9d1.sandbox.mit_living_wage_2025` GROUP BY 1
""").to_dataframe().to_string(index=False))

print("\n--- wage_type ---")
print(c.query("""
SELECT wage_type, COUNT(*) n FROM `strada-data-lab-c9d1.sandbox.mit_living_wage_2025`
GROUP BY 1 ORDER BY 1
""").to_dataframe().to_string(index=False))

print("\n--- Vermont (state + counties: region_id 50 / 50xxx) ---")
df = c.query("""
SELECT region_type, region_id, wage_type,
       `1_adult_0_children` AS a1c0,
       `1_adult_1_child`    AS a1c1,
       `1_adult_2_children` AS a1c2,
       `2_adults_both_working_0_children` AS a2w2c0,
       `2_adults_both_working_2_children` AS a2w2c2,
       `2_adults_1_working_2_children`    AS a2w1c2
FROM `strada-data-lab-c9d1.sandbox.mit_living_wage_2025`
WHERE region_id = 50 OR (region_id BETWEEN 50001 AND 50999)
ORDER BY region_type, region_id, wage_type
""").to_dataframe()
print(df.to_string(index=False))
df.to_csv("vt_living_wage.csv", index=False)
print("\nrows:", len(df))
