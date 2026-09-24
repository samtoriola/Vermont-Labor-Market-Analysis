"""Static checks for the Next.js app, standing in for `next build`.

Useful when Node is unavailable, or as a fast pre-commit sanity check. Verifies that
every import resolves, every data field referenced exists in the JSON, all views have
default exports and are wired into Dashboard, all chart components are exported,
'use client' is present wherever hooks or handlers are used, and no HTML attribute
names leaked into JSX.

Run from this scripts/ directory: python verify_app.py

Deliberately avoids os.stat: existence is checked against a scandir listing, so the
script still works if the repo ever sits behind Windows' 260-char MAX_PATH limit
(where stat fails on long paths but directory listing does not).
"""
import json, pathlib, re, sys, os

APP = pathlib.Path(__file__).resolve().parent.parent

# ---- build a listing-based index so no stat() is needed ----
INDEX = {}  # dir (as posix str) -> set of names
def walk(d):
    try:
        names = {e.name: e.is_dir() for e in os.scandir(d)}
    except OSError as e:
        print(f"  cannot scan {d}: {e}")
        return
    INDEX[pathlib.PurePath(d).as_posix()] = set(names)
    for n, isdir in names.items():
        if isdir and n not in ("node_modules", ".next", "out", ".git", ".vercel"):
            walk(os.path.join(d, n))

walk(str(APP))

def present(path):
    p = pathlib.PurePath(path)
    return p.name in INDEX.get(p.parent.as_posix(), set())

def read(path):
    # read through a handle opened relative to a short cwd chunk if needed
    try:
        return pathlib.Path(path).read_text(encoding="utf-8")
    except OSError:
        d = os.path.dirname(str(path))
        cur = os.getcwd()
        try:
            os.chdir(d)
            with open(os.path.basename(str(path)), encoding="utf-8") as f:
                return f.read()
        finally:
            os.chdir(cur)

js_files = [pathlib.PurePath(d) / n
            for d, names in INDEX.items()
            for n in names
            if n.endswith((".js", ".mjs"))]
js_files = sorted(js_files, key=lambda p: p.as_posix())
print(f"source files: {len(js_files)}")

problems = []

# ---- 1. relative and aliased imports resolve ----
for p in js_files:
    src = read(p)
    for m in re.finditer(r"""^import\s+(?:.+?\s+from\s+)?['"]([^'"]+)['"]""", src, re.M):
        spec = m.group(1)
        if spec.startswith("@/"):
            target = pathlib.PurePath(str(APP)) / spec[2:]
        elif spec.startswith("."):
            target = (p.parent / spec)
            parts = []
            for seg in target.as_posix().split("/"):
                if seg == ".":
                    continue
                if seg == "..":
                    parts.pop()
                else:
                    parts.append(seg)
            target = pathlib.PurePath("/".join(parts))
        else:
            continue
        ok = present(target) or any(
            present(target.with_suffix(e)) for e in (".js", ".jsx", ".json")
        )
        if not ok:
            problems.append(f"{p}: unresolved import '{spec}'")

# ---- 2. JSX attribute names React rejects ----
HTML_ATTRS = [
    (r'\bclass=', 'class= should be className='),
    (r'\bstroke-width=', 'stroke-width= should be strokeWidth='),
    (r'\bstroke-dasharray=', 'stroke-dasharray='),
    (r'\bstroke-linecap=', 'stroke-linecap='),
    (r'\bstroke-linejoin=', 'stroke-linejoin='),
    (r'\btext-anchor=', 'text-anchor= should be textAnchor='),
    (r'\bfont-size=', 'font-size= should be fontSize='),
    (r'\bfill-opacity=', 'fill-opacity= should be fillOpacity='),
    (r'\bviewbox=', 'viewbox= should be viewBox='),
    (r'\bcrossorigin=', 'crossorigin= should be crossOrigin='),
    (r'<label[^>]*\bfor=', 'for= should be htmlFor='),
]
for p in js_files:
    src = read(p)
    for pat, msg in HTML_ATTRS:
        for m in re.finditer(pat, src):
            problems.append(f"{p}:{src[:m.start()].count(chr(10))+1}: {msg}")

# ---- 3. 'use client' where hooks or handlers are used ----
for p in js_files:
    if "components" not in p.parts:
        continue
    src = read(p)
    if re.search(r"\buse(State|Effect|Context|Callback|Ref|Memo)\b|onClick=|onChange=", src):
        if not src.lstrip().startswith("'use client'"):
            problems.append(f"{p}: uses hooks/handlers but lacks 'use client'")

# ---- 4. every data field referenced exists ----
D = {}
for var, fn in [("DATA", "cps"), ("LC", "lightcast"), ("PCT", "percentiles"),
                ("SOW", "sow"), ("MAP", "vt-map")]:
    D[var] = json.loads(read(pathlib.PurePath(str(APP)) / "data" / f"{fn}.json"))
for p in js_files:
    src = read(p)
    for name, obj in D.items():
        for m in re.finditer(r"\b" + name + r"\.([A-Za-z_]\w*)", src):
            if m.group(1) not in obj:
                problems.append(
                    f"{p}:{src[:m.start()].count(chr(10))+1}: {name}.{m.group(1)} not in data")

# ---- 4b. known exports used but not imported (catches renames left half-done) ----
KNOWN = [
    "SERIES", "SERIES_HEX", "ORDINAL", "ORDINAL_HEX", "BRAND", "GOOD_HEX", "BAD_HEX",
    "LC", "PCT", "DATA", "SOW", "MAP", "TOTJ", "TIER_ORDER", "SIZE_ORDER", "DEFAULT_LW",
    "lwAnnual", "lwHourly", "tierRow", "cpsSubBacc", "cpsHsOrLess", "filterOcc",
    "occByFamily", "occByTier", "rampStep", "rampHex",
    "COMPARE", "PEOPLE", "wageStats", "occDots", "occBySize", "sizeBand", "compareCol",
    "fmt", "money", "pct", "niceMax", "trunc", "fmtVal",
    "useDrill", "occDrill", "useTip", "useTipHandlers",
    "RankedBars", "StackedRows", "Dumbbell", "TrendLine", "Scatter", "GroupedBars",
    "DotColumns", "DotRows", "DotLegend", "PercentileLadder", "LadderLegend",
    "occCols", "occDotTip", "personTip",
    "Panel", "Answer", "Callout", "VHead", "Legend", "Tiles", "Table", "N",
    "DrillHint", "LwPicker", "Filters", "VermontMap",
]
for p in js_files:
    src = read(p)
    imported = set()
    for m in re.finditer(r"^import\s+(.+?)\s+from\s+['\"]", src, re.M):
        clause = m.group(1)
        for nm in re.findall(r"[A-Za-z_]\w*", clause):
            imported.add(nm)
    # names declared in the file itself
    for m in re.finditer(r"(?:function|const|let|var|class)\s+([A-Za-z_]\w*)", src):
        imported.add(m.group(1))
    for m in re.finditer(r"export\s+function\s+([A-Za-z_]\w*)", src):
        imported.add(m.group(1))
    body = re.sub(r"^import[^;]+;", "", src, flags=re.M)
    for name in KNOWN:
        if re.search(r"" + name + r"", body) and name not in imported:
            problems.append(f"{p}: uses {name} but never imports or declares it")

# ---- 5. required files, views wired, default exports ----
for req in ["package.json", "next.config.mjs", "jsconfig.json", ".gitignore", "README.md",
            "app/layout.js", "app/page.js", "app/globals.css",
            "components/Dashboard.js", "components/Tooltip.js", "components/charts.js",
            "components/ui.js", "components/Drill.js", "components/Filters.js",
            "components/VermontMap.js", "lib/data.js", "lib/format.js", "lib/brand.js",
            "data/cps.json", "data/lightcast.json", "data/percentiles.json", "data/sow.json",
            "data/vt-map.json"]:
    if not present(pathlib.PurePath(str(APP)) / req):
        problems.append(f"MISSING required file: {req}")

dash = read(pathlib.PurePath(str(APP)) / "components/Dashboard.js")
VIEWS = ["Overview"] + [f"Q{i}" for i in range(1, 8)]
for q in VIEWS:
    if f"views/{q}" not in dash:
        problems.append(f"Dashboard.js does not import views/{q}")
    vp = pathlib.PurePath(str(APP)) / "components" / "views" / f"{q}.js"
    if not present(vp):
        problems.append(f"missing components/views/{q}.js")
    elif "export default function" not in read(vp):
        problems.append(f"views/{q}.js has no default export")

# ---- 6. chart components exported and used ----
charts_src = read(pathlib.PurePath(str(APP)) / "components/charts.js")
for comp in ["RankedBars", "StackedRows", "Dumbbell", "TrendLine", "Scatter",
             "GroupedBars"]:
    if f"export function {comp}" not in charts_src:
        problems.append(f"charts.js does not export {comp}")

dots_src = read(pathlib.PurePath(str(APP)) / "components/dots.js")
for comp in ["DotColumns", "DotRows", "DotLegend", "PercentileLadder", "LadderLegend"]:
    if f"export function {comp}" not in dots_src:
        problems.append(f"dots.js does not export {comp}")

# ---- 7. path-length audit (the real deployment blocker) ----
base = os.path.abspath(str(APP))
longest = max(js_files, key=lambda p: len(os.path.abspath(str(p))))
print(f"project root: {len(base)} chars")
print(f"longest source path: {len(os.path.abspath(str(longest)))} chars ({longest.name})")
over = [p for p in js_files if len(os.path.abspath(str(p))) > 260]
if over:
    print(f"!! {len(over)} file(s) already exceed Windows MAX_PATH (260):")
    for p in over:
        print(f"     {len(os.path.abspath(str(p)))}  {p}")

print()
if problems:
    print(f"!! {len(problems)} PROBLEM(S):")
    for x in problems:
        print("   ", x)
else:
    print("All structural checks passed.")
sys.exit(1 if problems else 0)
