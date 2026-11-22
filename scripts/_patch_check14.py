"""check_workfiles walks the new home-page link in the chain.

The tiles now name a workfile each, which is a promise: open that file and the
figure is there. So the check opens them -- 14's four values against 00 and 15,
and every workfile a tile names against the folder -- and then reads the four
figures off the home page itself.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "check_workfiles.py")
s = io.open(P, encoding="utf-8").read()

subs = [
    ('''head = {r["figure"]: num(r["value"]) for r in read("00_headline_figures.csv")}''',
     '''head = {r["figure"]: num(r["value"]) for r in read("00_headline_figures.csv")}
tiles = read("14_home_tiles.csv")
lforce = {r["measure"]: num(r["value"]) for r in read("15_labor_force_cps.csv")}'''),

    ('''# ---- and the headline figures are what the dashboard prints ----------------''',
     '''print("--- 14 agrees with 00, and the files it names exist ---")
for t in tiles:
    want = head.get(t["tile"])
    if want is None:
        fails.append("14 has a tile 00 does not list: %s" % t["tile"])
    else:
        close(num(t["value"]), want, 1, "tile %s" % t["tile"])
    wf = t["workfile_to_check"]
    if not os.path.exists(os.path.join(WF, wf)):
        fails.append("the %s tile points at %s, which is not in workfiles/" % (t["tile"], wf))
close(lforce.get("Employed"), head.get("Employed Vermonters"), 1, "15 Employed against 00")
close(lforce.get("Employed", 0) + lforce.get("Unemployed", 0), lforce.get("Labor force"), 1,
      "15 employed + unemployed against the labor force")
print("  %d tiles, each naming a workfile that exists" % len(tiles))

# 01 is the detailed export and the statewide total is not: anyone summing 01 to
# check the home tile should land 1,450 short, and 00 should say so.
close(head.get("Jobs in the charted occupations"),
      head.get("Jobs with a published pay ladder"), 1,
      "01's job total against the priced total")
if head.get("Jobs, 2025", 0) <= head.get("Jobs in the charted occupations", 0):
    fails.append("00 no longer shows the statewide total above the charted total")
else:
    print("  statewide %s, charted %s, gap %s"
          % ("{:,.0f}".format(head["Jobs, 2025"]),
             "{:,.0f}".format(head["Jobs in the charted occupations"]),
             "{:,.0f}".format(head["Jobs, 2025"] - head["Jobs in the charted occupations"])))

# ---- and the headline figures are what the dashboard prints ----------------'''),

    ('''        want = [
            ("Overview", "{:,.0f}".format(head["Jobs with a published pay ladder"]),
             "jobs with a published pay ladder"),''',
     '''        want = [
            ("Home", "{:,.0f}".format(head["Jobs, 2025"]), "the jobs tile"),
            ("Home", "{:,.0f}".format(head["Employed Vermonters"]),
             "the employed-Vermonters tile"),
            ("Home", "{:,.0f}".format(head["Annual openings"]), "the openings tile"),
            ("Home", "{:,.0f}".format(head["VSCS completions, 2024"]),
             "the completions tile"),
            ("Overview", "{:,.0f}".format(head["Jobs with a published pay ladder"]),
             "jobs with a published pay ladder"),'''),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("%d occurrences of %r" % (s.count(old), old[:90]))
for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("check_workfiles.py patched,", len(s), "bytes")
