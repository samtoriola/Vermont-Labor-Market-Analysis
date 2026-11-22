"""Adds the register-coverage check to verify_app.py. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_app.py")
s = io.open(P, encoding="utf-8").read()

ANCHOR = "# ---- 7. path-length audit (the real deployment blocker) ----"
assert s.count(ANCHOR) == 1

LINES = [
    '# ---- 6b. the Methods source register covers every section ----',
    '# Methods carries a row per section saying what it draws and which file it reads.',
    '# The rows name each section in prose, so renaming one in lib/nav.js leaves a row',
    '# pointing at a section that no longer exists, and nothing else would catch it.',
    'nav_src = read(pathlib.PurePath(str(APP)) / "lib/nav.js")',
    '# Hidden sections are commented out in nav.js and are not in the app, so they',
    '# are not in the register either.',
    'nav_src = re.sub(r"^\s*//.*$", "", nav_src, flags=re.M)',
    'methods_src = read(pathlib.PurePath(str(APP)) / "components/views/Methods.js")',
    'ITEM = re.compile(r"\\{\\s*id:\\s*\'[^\']+\',\\s*label:\\s*\'([^\']+)\'\\s*\\}")',
    'for g in re.findall(r"label:\\s*\'([^\']+)\',\\s*\\n\\s*blurb:", nav_src):',
    '    seg = nav_src.split("label: \'%s\'," % g, 1)[1].split("kind: \'group\'", 1)[0]',
    '    for lab in ITEM.findall(seg):',
    '        row = "%s \\u00b7 %s" % (g, lab)',
    '        if row not in methods_src:',
    '            problems.append("Methods has no source-register row for %r" % row)',
    'if "\'Overview\'," not in methods_src:',
    '    problems.append("Methods has no source-register row for the Overview")',
    '',
    '',
]
s = s.replace(ANCHOR, "\n".join(LINES) + ANCHOR)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verify_app.py patched")
