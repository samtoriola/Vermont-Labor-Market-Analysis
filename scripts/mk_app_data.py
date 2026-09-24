"""Copy the generated *_data.js globals into the app's data/ folder as plain JSON.

Run from this scripts/ directory, after the four build scripts have produced their
*_data.js files here. Output goes to ../data/, which is what lib/data.js imports.
"""
import json, os, pathlib

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE.parent / "data"
DATA.mkdir(parents=True, exist_ok=True)

PAIRS = [
    ("dash_data.js", "cps.json"),
    ("lc_data.js", "lightcast.json"),
    ("pct_data.js", "percentiles.json"),
    ("sow_data.js", "sow.json"),
]

# The four build scripts have independent inputs, so a change to one of them should
# not force a BigQuery run for the other three. Convert whatever is present and say
# plainly which committed JSONs were left alone.
present = [(s, d) for s, d in PAIRS if (HERE / s).exists()]
absent = [(s, d) for s, d in PAIRS if not (HERE / s).exists()]
if not present:
    raise SystemExit(
        "No generated *_data.js files here. Run the build scripts first - "
        "see scripts/README.md for the order."
    )

for src, dst in present:
    text = (HERE / src).read_text(encoding="utf-8")
    obj = json.loads(text[text.index("=") + 1: text.rindex(";")].strip())
    out = DATA / dst
    out.write_text(json.dumps(obj, indent=0, separators=(",", ":")), encoding="utf-8")
    print(f"{src:16s} -> data/{dst:18s} {os.path.getsize(out):>8,} bytes  "
          f"top-level keys: {len(obj)}")


for src, dst in absent:
    have = (DATA / dst).exists()
    print(f"{src:16s} -- not generated; data/{dst} "
          + ("left as committed" if have else "IS MISSING, the app will not build"))

total = sum(os.path.getsize(DATA / d) for _, d in PAIRS if (DATA / d).exists())
print(f"\ntotal data: {total:,} bytes ({total/1e6:.2f} MB)")
print(f"written to: {DATA}")
