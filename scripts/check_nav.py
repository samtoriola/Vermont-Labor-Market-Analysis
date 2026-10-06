"""nav.js must match the sections the views actually declare.

A label that drifts shows a sidebar entry which opens the wrong panel, and nothing
else in the toolchain would notice: the build compiles and every section still renders.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FILES = {'overview': 'Overview.js', 'regions': 'Q7.js', 'structure': 'Q1.js',
         'wage': 'Q2.js', 'demand': 'Q3.js', 'pathways': 'Q4.js',
         'opportunity': 'Q5.js', 'alignment': 'Q6.js', 'about': 'About.js',
         'methods': 'Methods.js'}

nav_src = (ROOT / 'lib' / 'nav.js').read_text(encoding='utf-8')
nav = {}
for m in re.finditer(r"view: '([^']+)',\s*\n\s*label: '[^']*',(.*?)(?=\n  \{|\n\];)",
                     nav_src, re.S):
    view, body = m.group(1), m.group(2)
    nav[view] = re.findall(r"\{ id: '([^']+)', label: '([^']*)' \}", body)

problems = []
for view, fn in FILES.items():
    src = (ROOT / 'components' / 'views' / fn).read_text(encoding='utf-8')
    actual = re.findall(r"id: '([^']+)',\s*\n\s*label: '([^']*)'", src)
    declared = nav.get(view, [])
    if actual != declared:
        problems.append(f"{view} ({fn}):")
        problems.append(f"    view: {actual}")
        problems.append(f"    nav : {declared}")

print(f"checked {len(FILES)} views against lib/nav.js")
if problems:
    print("\n!! nav.js is out of step with the views:")
    for p in problems: print("   ", p)
    sys.exit(1)
print("nav.js matches every view's sections.")
