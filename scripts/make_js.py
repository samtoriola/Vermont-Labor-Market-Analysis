import json

d = json.load(open("cps_vt_dashboard_data.json"))

PATH_ORDER = ["Less than high school", "High school diploma", "Some college, no degree",
              "Associate degree (sub-baccalaureate)", "Bachelor's degree",
              "Graduate or professional degree"]

fam = [r for r in d["by_family"] if r["family"] not in ("Unclassified", "Military")]
fam.sort(key=lambda r: -r["avg_employment"])

out = {
    "months": d["n_months"],
    "families": [{"f": r["family"], "e": round(r["avg_employment"]), "n": int(r["n_unweighted"]),
                  "u": int(r["uniq_persons"])} for r in fam],
    "sectors": [{"s": r["sector"], "e": round(r["avg_employment"]), "n": int(r["n_unweighted"])}
                for r in d["by_sector"] if r["sector"] not in ("Unclassified", "Military")],
    "pathways": [],
    "famEdu": {},
    "trend": [{"y": int(r["YEAR"]), "m": int(r["months"]), "emp": round(r["employment"]),
               "lf": round(r["labor_force"]), "ur": round(r["unemp_rate"] * 100, 2),
               "ba": round(r["ba_plus_share_25p"] * 100, 1)} for r in d["annual_trend"]],
    "famTrend": {},
    "famSector": [],
}

tot_p = sum(r["avg_employment"] for r in d["by_pathway"] if r["pathway"] != "Unknown")
for name in PATH_ORDER:
    r = next((x for x in d["by_pathway"] if x["pathway"] == name), None)
    if r:
        out["pathways"].append({"p": name, "e": round(r["avg_employment"]),
                                "n": int(r["n_unweighted"]),
                                "sh": round(r["avg_employment"] / tot_p * 100, 1)})

for r in d["family_x_education"]:
    f, p = r["family"], r["pathway"]
    if f in ("Unclassified", "Military") or p == "Unknown":
        continue
    out["famEdu"].setdefault(f, {})[p] = {"e": round(r["avg_employment"]), "n": int(r["n_unweighted"])}

for r in d["family_trend"]:
    f = r["family"]
    if f in ("Unclassified", "Military"):
        continue
    out["famTrend"].setdefault(f, {})[int(r["YEAR"])] = {
        "e": round(r["avg_employment"]), "n": int(r["n_unweighted"])}

seen = {}
for r in d["family_x_sector"]:
    if r["family"] in ("Unclassified", "Military") or r["sector"] in ("Unclassified", "Military"):
        continue
    seen.setdefault(r["family"], []).append(
        {"s": r["sector"], "e": round(r["avg_employment"]), "n": int(r["n_unweighted"])})
out["famSector"] = {k: sorted(v, key=lambda x: -x["e"])[:4] for k, v in seen.items()}

with open("dash_data.js", "w") as f:
    f.write("const DATA = " + json.dumps(out, separators=(",", ":")) + ";\n")

print("families:", len(out["families"]), "sectors:", len(out["sectors"]))
print("pathways:", [(p["p"], p["sh"]) for p in out["pathways"]])
print("total emp 2021-25 avg:", sum(r["e"] for r in out["families"]))
import os
print("dash_data.js bytes:", os.path.getsize("dash_data.js"))
