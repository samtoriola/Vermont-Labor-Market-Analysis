"""Split the two reference tabs cleanly.

About orients: what this is, where to look, how to drive it. Methods defines: what a
measure means and what rule was applied. Every factual caveat belongs in Methods once,
so About's "Reading the numbers" panel went -- three of its four entries restated
Methods (jobs vs workers, the small-base rule, the completions allocation) and the
fourth, projections, was a measure definition that belonged in Methods anyway.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- About
p = ROOT / "components" / "views" / "About.js"
s = p.read_text(encoding="utf-8")

# Drop the duplicated caveats panel outright.
a = s.index('      <Panel title="Reading the numbers">')
b = s.index('      <Panel title="Keeping it current">')
s = s[:a] + s[b:]

# Fold the two "Keeping it current" lines into Purpose; one panel less to scroll.
a = s.index('      <Panel title="Keeping it current">')
b = s.index("    </>", a)
s = s[:a] + s[b:]

s = s.replace(
    """            [
              'What it is not',
              'Not a forecast and not a program recommendation. It reports what the sources say and states where they disagree; every figure is a measurement with a stated universe, not a conclusion.',
            ],""",
    """            [
              'What it is not',
              'Not a forecast and not a program recommendation. It reports what the sources say and states where they disagree.',
            ],
            [
              'Not live',
              'Build scripts pull from BigQuery and the Lightcast exports and write a small set of JSON files that the app reads at build time. Numbers change only when a script is re-run and the app redeployed.',
            ],
            [
              'Where the detail is',
              'Sources, measure definitions and every suppression rule are on the Methods \\u0026 limits tab. Each panel also carries its own source line.',
            ],""",
)

# The living-wage default lives in Methods; here it only needs to say where the control
# is and what it moves.
s = s.replace(
    "'Wage quality and Pathways carry a household selector. It changes every figure that"
    " compares pay with self-sufficiency, so set it before reading those tabs. The default"
    " is one adult with no children.',",
    "'Wage quality and Pathways carry a household selector. It moves every figure that"
    " compares pay with self-sufficiency, so set it before reading those tabs.',",
)

# Period is orientation here; the per-source vintages are in the Methods sources table.
s = s.replace(
    "`Employment and wages are 2025. Change is measured over 2021–2025, projections"
    " run to 2030, and job postings cover ${LC.postWindow}. Credential production is the"
    " 2024 academic year.`",
    "`Employment and wages are 2025, change is measured over 2021–2025, and"
    " projections run to 2030.`",
)
p.write_text(s, encoding="utf-8")
print("About: dropped the caveats panel, folded in the two operational lines")

# ---------------------------------------------------------------- Methods
m = ROOT / "components" / "views" / "Methods.js"
t = m.read_text(encoding="utf-8")

# Projections arrive from About, where they did not belong.
old = """            [
              'Opportunity index',"""
new = """            [
              'Projected growth',
              'A Lightcast model of change to 2030, not an observation. Change over 2021–2025 is what happened, and the two are kept in separate panels for that reason.',
            ],
            [
              'Opportunity index',"""
assert old in t
t = t.replace(old, new, 1)

# Three consecutive CPS entries said "CPS" three times; the LAUS note folds into the
# precision entry it qualifies.
old_u = """            [
              'Unemployment',
              'The rate shown is the direct CPS estimate. Vermont’s official rate comes from LAUS, which is model-based, so the two differ by construction rather than by error.',
            ],"""
assert old_u in t
t = t.replace(old_u, "")
t = t.replace(
    "and rate intervals use the person count, not the record count, because the survey"
    " re-interviews the same households.',",
    "and rate intervals use the person count, not the record count, because the survey"
    " re-interviews the same households. The unemployment rate shown is the direct CPS"
    " estimate; Vermont’s official rate comes from the model-based LAUS series, so"
    " the two differ by construction.',",
)
m.write_text(t, encoding="utf-8")
print("Methods: projections added, unemployment folded into CPS precision")
