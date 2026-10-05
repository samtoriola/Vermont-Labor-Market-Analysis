"""Flag ALL_CAPS identifiers used in code but never imported or declared.

This catches a half-finished rename. A stale `SER` left behind after renaming to
`SERIES` passes every other static check and the production build — it only fails at
runtime, when the component that touches it unmounts the page.

Only expression positions count: the identifier must be followed by a property access,
an index, or a call. Prose acronyms in JSX text (CPS, NAICS, IPEDS, VSCS) are not code
and are ignored, which is why a plain word-boundary match is useless here.

Run from scripts/:  python check_idents.py
"""
import os
import pathlib
import re
import sys

APP = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {"node_modules", ".next", "out", ".git", ".vercel", "scripts", "data"}

# Legitimately bare: short locals, globals, and prose acronyms that can be followed
# by a dot inside a <code> span or a filename.
ALLOW = {
    "NS", "V", "W", "H", "PAD", "TOL", "URL", "JSON", "Math", "Object", "Array",
    "NaN", "Infinity", "M", "R", "D", "P", "X", "Y", "OK",
    "CPS", "ACS", "IPEDS", "IPUMS", "NAICS", "SOC", "CIP", "VSCS", "CCV", "MIT",
    "BA", "HS", "LW", "LMI", "PUMA", "SOW", "US",
    # SQL fragments that appear inside source-line captions
    "SUM", "COUNT", "AVG", "WTFINL", "PERWT", "MAJORNUM", "CIPCODE",
    # Agency and survey names that appear in source captions
    "OEWS", "BLS", "LAUS", "OES", "USA", "CSV", "TIGER", "NAICS",
}

# The import clause may run over several lines, so match lazily across newlines
# rather than anchoring to one line -- a multi-line import used to read as "never
# imported", which buried real findings under false positives.
IMPORT_RE = re.compile(r"^import\s+([\s\S]+?)\s+from\s+['\"]", re.M)
DECL_RE = re.compile(r"\b(?:const|let|var|function|class)\s+([A-Za-z_]\w*)")
DESTRUCT_RE = re.compile(r"\b(?:const|let|var)\s*\{([^}]*)\}")
WORD_RE = re.compile(r"[A-Za-z_]\w*")
# ALL_CAPS used as a value: followed by .prop, [index] or (call) -- or standing
# alone as an argument or operand, which is how `f(top, TOTJ, n)` reads. That last
# shape used to slip through and fail only at runtime, which is the whole point of
# this check: a missing import there unmounts the view and the build says nothing.
USE_RE = re.compile(
    r"\b([A-Z][A-Z_0-9]+)"
    r"(?=\s*\.\s*[A-Za-z_]|\s*\[|\s*\(|\s*[,)]|\s*[-+*/<>]|\s*===?)"
)


def sources():
    for d, dirs, files in os.walk(APP):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith((".js", ".jsx", ".mjs")):
                yield pathlib.Path(d) / f


def strip_comments(src):
    src = re.sub(r"//[^\n]*", "", src)
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


problems = []
checked = 0

for path in sources():
    raw = path.read_text(encoding="utf-8")
    checked += 1

    declared = set(ALLOW)
    for m in IMPORT_RE.finditer(raw):
        declared.update(WORD_RE.findall(m.group(1)))
    declared.update(DECL_RE.findall(raw))
    for m in DESTRUCT_RE.finditer(raw):
        declared.update(WORD_RE.findall(m.group(1)))

    # Import and re-export clauses list names rather than use them. With the widened
    # pattern a bare `A, B` in `export { A, B } from ...` would read as a use.
    stripped = re.sub(r"^import[\s\S]*?;", "", raw, flags=re.M)
    stripped = re.sub(r"^export\s*\{[^}]*\}\s*from[^;]*;", "", stripped, flags=re.M)
    body = strip_comments(stripped)

    seen = set()
    for m in USE_RE.finditer(body):
        name = m.group(1)
        if name in declared or name in seen:
            continue
        seen.add(name)
        line = body[: m.start()].count("\n") + 1
        problems.append(f"{path.relative_to(APP)}:{line}: {name} never imported or declared")

print(f"checked {checked} source files")
if problems:
    print(f"\n!! {len(problems)} PROBLEM(S):")
    for p in problems:
        print("   ", p)
    sys.exit(1)
print("No undefined identifiers in expression position.")
