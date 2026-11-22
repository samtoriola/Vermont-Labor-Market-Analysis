"""Brings About up to the current app. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "components", "views", "About.js")
s = io.open(P, encoding="utf-8").read()


def sub(old, new, n=1):
    global s
    assert s.count(old) == n, "%d occurrences of %r" % (s.count(old), old[:70])
    s = s.replace(old, new)


# ---- the Overview no longer carries the jobs-require vs workers-hold panel ---
sub("""            {
              cells: [
                'Overview',
                'Headline scale of the labor market, and the gap between what jobs require and what workers hold',
              ],
            },""",
    """            {
              cells: [
                'Overview',
                'The whole labor market on one chart: every occupation group by size, shaded by how much of its work pays below a living wage',
              ],
            },""")

# ---- the sidebar says Employment, so this should too ------------------------
sub("""                'Employment structure',
                'Which occupation groups and industries employ Vermonters, and what each pays',""",
    """                'Employment',
                'Which occupation groups and industries employ Vermonters, and what each pays',""")

# ---- Wage quality gained the county section ---------------------------------
sub("""                'Wage quality',
                'How much of the work pays less than a self-sufficiency benchmark, and where that bites hardest',""",
    """                'Wage quality',
                'How much of the work pays less than a self-sufficiency benchmark, and how that changes when each county is measured against its own cost floor',""")

# ---- the selector and the drill-down both reach further than this said -------
sub("""            [
              'Set the living wage first',
              'Wage quality, Pathways, Workers and Regions carry a household selector. It moves every figure that compares pay with self-sufficiency, so set it before reading those tabs.',
            ],
            [
              'Click through to the detail',
              'Bars, dot columns and table rows that sit on underlying occupations open a detail panel when clicked. Employment structure, Wage quality, Pathways and VSCS alignment all support it.',
            ],""",
    """            [
              'Set the living wage first',
              'The Overview, Wage quality, Pathways, Workers, Opportunities and Regions all carry a household selector. It moves every figure that compares pay with self-sufficiency, so set it before reading those tabs. The default is one adult with no children, which is the only household MIT publishes for every county.',
            ],
            [
              'Click through to the detail',
              'Bars and table rows that sit on underlying occupations open a panel beside the chart, with that row’s figures and its largest occupations. A link in the panel opens the whole table. The Overview, Employment, Wage quality, Demand & growth, Pathways and VSCS alignment all support it.',
            ],
            [
              'Check where a number came from',
              'Every chart carries a source line underneath it, written in plain words rather than by vendor. Methods holds the key to those names and a row per section saying what it draws, which source it came from, and which file the app reads.',
            ],""")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("About.js patched,", len(s), "bytes")
