"""Vermont / New Hampshire / United States wage distributions for the dot plot.

Each dot in the chart is ONE OCCUPATION positioned at its median wage, sized by
employment -- not one worker. The reference visual plots individual graduate incomes
from record-level microdata; OEWS publishes five percentiles per occupation, so
occupation-level dots are the honest equivalent. Nothing here is simulated.

New Hampshire is the neighbour comparison: same OEWS vintage (2025 state file) and a
similar small-state labour market. The US column comes from the 2024 national file --
a year older, which is flagged in the UI.
"""
import json, os, pathlib
import numpy as np
import pandas as pd
import warnings
from google.cloud import bigquery

warnings.filterwarnings("ignore")
c = bigquery.Client(project="strada-data-lab-c9d1")

HERE = pathlib.Path(__file__).resolve().parent
PCTS = ["p10", "p25", "p50", "p75", "p90"]
CENSOR = 239200.0  # OEWS '#' means at or above this


def clean(series):
    """OEWS numerics arrive as strings with commas; '*' = suppressed, '#' = top-coded."""
    s = series.astype(str).str.strip().str.replace(",", "", regex=False)
    s = s.replace({"*": np.nan, "#": str(CENSOR), "": np.nan, "nan": np.nan, "None": np.nan})
    return pd.to_numeric(s, errors="coerce")


def pull(sql, area):
    df = c.query(sql).to_dataframe()
    out = pd.DataFrame({
        "soc": df["OCC_CODE"].astype(str),
        "name": df["OCC_TITLE"].astype(str),
        "emp": clean(df["TOT_EMP"]),
        "mean": clean(df["A_MEAN"]),
        "p10": clean(df["A_PCT10"]),
        "p25": clean(df["A_PCT25"]),
        "p50": clean(df["A_MEDIAN"]),
        "p75": clean(df["A_PCT75"]),
        "p90": clean(df["A_PCT90"]),
    })
    out["area"] = area
    before = len(out)
    out = out[out["p50"].notna() & out["emp"].notna() & (out["emp"] > 0)]
    print(f"  {area}: {len(out)} of {before} detailed occupations priced, "
          f"{out['emp'].sum():,.0f} jobs")
    return out


STATE = """
SELECT OCC_CODE, OCC_TITLE, TOT_EMP, A_MEAN, A_PCT10, A_PCT25, A_MEDIAN, A_PCT75, A_PCT90
FROM `strada-data-lab-c9d1.sandbox.bls_oews_state_2025`
WHERE AREA_TYPE = 2 AND O_GROUP = 'detailed' AND PRIM_STATE = '{st}'
"""
NATIONAL = """
SELECT OCC_CODE, OCC_TITLE, TOT_EMP, A_MEAN, A_PCT10, A_PCT25, A_MEDIAN, A_PCT75, A_PCT90
FROM `strada-data-lab-c9d1.sandbox.bls_oews_national_2024`
WHERE O_GROUP = 'detailed'
"""

print("pulling OEWS:")
vt = pull(STATE.format(st="VT"), "Vermont")
nh = pull(STATE.format(st="NH"), "New Hampshire")
us = pull(NATIONAL, "United States")

AREAS = [
    ("Vermont", vt, "OEWS state, 2025"),
    ("New Hampshire", nh, "OEWS state, 2025"),
    ("United States", us, "OEWS national, 2024"),
]

out = {"censorAt": CENSOR, "areas": []}
for label, df, src in AREAS:
    w = df["emp"]
    # Employment-weighted mean of occupation medians: the "average" line on the chart.
    avg = float(np.average(df["p50"], weights=w))

    # True employment-weighted median across occupations, for the tooltip. Different
    # from the average, and the gap is the point of the chart.
    o = df.sort_values("p50")
    cw = o["emp"].cumsum()
    med = float(np.interp(cw.iloc[-1] / 2, cw, o["p50"]))

    dots = [
        {
            "n": r["name"],
            "s": r["soc"],
            "e": round(float(r["emp"])),
            "v": round(float(r["p50"])),
            "lo": (round(float(r["p10"])) if pd.notna(r["p10"]) else None),
            "hi": (round(float(r["p90"])) if pd.notna(r["p90"]) else None),
            "mu": (round(float(r["mean"])) if pd.notna(r["mean"]) else None),
        }
        for _, r in df.sort_values("emp", ascending=False).iterrows()
    ]

    out["areas"].append({
        "label": label,
        "src": src,
        "avg": round(avg),
        "med": round(med),
        "nOcc": len(df),
        "emp": round(float(w.sum())),
        "p10": round(float(np.average(df["p10"].fillna(df["p50"]), weights=w))),
        "p90": round(float(np.average(df["p90"].fillna(df["p50"]), weights=w))),
        "dots": dots,
    })
    print(f"  {label:15s} avg={avg:>8,.0f}  wtd median={med:>8,.0f}  dots={len(dots)}")

# Per-occupation ladder for Vermont: mean and median on one scale, so the chart can
# show where the average sits inside the spread instead of hiding it in a box.
out["vtLadder"] = {
    r["soc"]: {
        "mu": (round(float(r["mean"])) if pd.notna(r["mean"]) else None),
        "p10": (round(float(r["p10"])) if pd.notna(r["p10"]) else None),
        "p25": (round(float(r["p25"])) if pd.notna(r["p25"]) else None),
        "p50": round(float(r["p50"])),
        "p75": (round(float(r["p75"])) if pd.notna(r["p75"]) else None),
        "p90": (round(float(r["p90"])) if pd.notna(r["p90"]) else None),
    }
    for _, r in vt.iterrows()
}
nmu = sum(1 for v in out["vtLadder"].values() if v["mu"] is not None)
print("")
print(f"vtLadder: {len(out['vtLadder'])} Vermont occupations, {nmu} with a mean wage")

# A fixed round ceiling, shared with the person-level chart so the two read on the
# same scale. Dots above it are drawn pinned at the top edge rather than dropped.
allv = np.array([d["v"] for a in out["areas"] for d in a["dots"]])
out["yMax"] = 200000
out["yMaxAbs"] = float(allv.max())
print(f"y-scale: 0 to {out['yMax']:,}; "
      f"{(allv <= out['yMax']).mean()*100:.1f}% of dots on scale, "
      f"{int((allv > out['yMax']).sum())} above, max {allv.max():,.0f}")

p = HERE.parent / "data" / "compare.json"
p.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print(f"wrote {p} ({os.path.getsize(p):,} bytes)")
