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

missing = [src for src, _ in PAIRS if not (HERE / src).exists()]
if missing:
    raise SystemExit(
        "Missing generated file(s): " + ", ".join(missing) +
        "\nRun the build scripts first - see scripts/README.md for the order."
    )

for src, dst in PAIRS:
    text = (HERE / src).read_text(encoding="utf-8")
    obj = json.loads(text[text.index("=") + 1: text.rindex(";")].strip())
    out = DATA / dst
    out.write_text(json.dumps(obj, indent=0, separators=(",", ":")), encoding="utf-8")
    print(f"{src:16s} -> data/{dst:18s} {os.path.getsize(out):>8,} bytes  "
          f"top-level keys: {len(obj)}")

total = sum(os.path.getsize(DATA / d) for _, d in PAIRS)
print(f"\ntotal data: {total:,} bytes ({total/1e6:.2f} MB)")
print(f"written to: {DATA}")
