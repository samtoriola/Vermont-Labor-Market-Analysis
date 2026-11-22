"""The index changed, so the places that describe it have to change with it.

Including Methods, which gains the correlation. A register that describes the
score without saying that one of its four legs leans on another is describing a
different score from the one on screen.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

EDITS = {
    "components/views/Q5.js": [
        ("""                  One score per occupation, the average of four percentile ranks: how many
                  it employs, how fast it is growing, how heavily it is advertised, and
                  what it pays.""",
         """                  One score per occupation, the average of four percentile ranks: how many
                  it employs, how fast it is growing, how little of it has to be replaced
                  each year, and what it pays.""", 1),
    ],
    "components/views/About.js": [
        ("'Occupations scoring highest on scale, growth, advertised demand and pay, each bar split into the four ranks the score is the mean of'",
         "'Occupations scoring highest on scale, growth, stability and pay, each bar split into the four ranks the score is the mean of'", 1),
    ],
    "components/views/Methods.js": [
        ("'Mean of four percentile ranks, 25% each: employment, projected growth, postings per 100 jobs, median pay. Occupations with 100+ jobs and a published wage.'",
         "'Mean of four percentile ranks, 25% each: employment, projected growth, stability, median pay. Occupations with 100+ jobs and a published wage. Stability is the replacement rate inverted — an occupation replacing less of its workforce each year ranks higher — and it replaced postings per 100 jobs at the November 2025 review. Read it knowing that it ranks r = +0.611 against pay, where postings ranked +0.394: Vermont’s high-replacement work is its low-paid work, and inverting the sign flips that relationship rather than removing it, so the pay dimension carries more of this score than its quarter. The panel shows all four ranks for that reason.'", 1),
    ],
}

loaded = []
for rel, pairs in EDITS.items():
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _, want in pairs:
        if s.count(old) != want:
            raise SystemExit("%s: %d of %r" % (rel, s.count(old), old[:60]))
    loaded.append((p, rel, s, pairs))

for p, rel, s, pairs in loaded:
    for old, new, _ in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("%-30s patched" % rel)
