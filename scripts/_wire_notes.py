"""Attach a computed note to each panel that has an honest comparison to make."""
import pathlib
import sys

V = pathlib.Path(__file__).resolve().parent.parent / "components" / "views"

# view -> (extra imports, [(panel title fragment, note expression)])
WIRE = {
    "Overview": (
        ["requirementsGap"],
        [("Do Vermont’s jobs ask for the credentials", "requirementsGap(baReq, lastCps.ba)")],
    ),
    "Q1": (
        ["familyConcentration", "credentialSpread"],
        [
            ("Which occupational families employ the most", "familyConcentration(fams, TOTJ)"),
            ("What credential does each family ask for", "credentialSpread(fams)"),
        ],
    ),
    "Q2": (
        ["sizePayStep", "topOccShare", "meanAboveMedian"],
        [
            ("How does pay spread within large, medium", "sizePayStep(PCT.sizeTiers, SIZE_ORDER)"),
            ("Which 25 occupations employ the most", "topOccShare(top, TOTJ2, LC.allOcc.length)"),
            ("In the largest occupations, how far is the average", "meanAboveMedian(ladder)"),
        ],
    ),
    "Q3": (
        ["demandDivergence", "observedSplit", "growthSplit"],
        [
            ("Do jobs, openings and postings point at the same", "demandDivergence(align)"),
            ("Which families grew, and which shrank", "observedSplit(fams)"),
            ("Which families are projected to grow", "growthSplit(fams)"),
        ],
    ),
    "Q4": (
        ["ladderStep", "peopleLadderStep", "livingWageJump", "largestCategory"],
        [
            ("What does each rung pay, by what the job asks", "ladderStep(LC.tiers, TIER_ORDER)"),
            ("What does each rung pay, by the credential workers", "peopleLadderStep(PEOPLE.byCred)"),
            ("Which credential levels clear the living wage", "livingWageJump(LC.tiers, TIER_ORDER, lw)"),
            ("What sits inside each of the five tiers", "largestCategory(LC.eduDetail)"),
        ],
    ),
    "Q5": (
        ["topScoreCredentials"],
        [("Which occupations combine scale, growth, demand", "topScoreCredentials(O.top)")],
    ),
    "Q6": (
        ["awardMix", "familiesNoCompletions"],
        [
            ("What credentials does VSCS award", "awardMix(V.byAward, V.totalCompletions)"),
            ("Where does VSCS production line up with openings", "familiesNoCompletions(V.byFamily)"),
        ],
    ),
    "Q7": (
        ["countySpread", "countyIncomeRange"],
        [
            ("How does opportunity differ across Vermont", "countySpread(R)"),
            ("How does each county compare", "countyIncomeRange(R)"),
        ],
    ),
}

for name, (imports, pairs) in WIRE.items():
    p = V / f"{name}.js"
    s = p.read_text(encoding="utf-8")

    have = []
    if "from '@/lib/insight'" in s:
        a = s.index("import {", s.index("from '@/lib/insight'") - 200)
        b = s.index("}", a)
        have = [x.strip() for x in s[a + 8:b].split(",") if x.strip()]
        s = s[:a] + "import { " + ", ".join(sorted(set(have + imports))) + " }" + s[b + 1:]
    else:
        anchor = "import Sections from '../Sections';"
        if anchor not in s:
            sys.exit(f"{name}: no Sections import to anchor on")
        s = s.replace(
            anchor,
            anchor + "\nimport { " + ", ".join(imports) + " } from '@/lib/insight';",
        )

    for frag, expr in pairs:
        hits = [ln for ln in s.split("\n") if "title=" in ln and frag in ln]
        if len(hits) != 1:
            sys.exit(f"{name}: {len(hits)} titles match {frag!r}")
        line = hits[0]
        indent = " " * (len(line) - len(line.lstrip()))
        s = s.replace(line, line + "\n" + indent + "note={" + expr + "}", 1)

    p.write_text(s, encoding="utf-8")
    print(f"  {name}: {len(pairs)} note(s)")
