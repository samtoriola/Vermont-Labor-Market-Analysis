"""Hides Workers and Program candidates. Throwaway.

Both follow the convention already in lib/nav.js: the entry is commented out with
a note saying what it was and how to bring it back, and the view code stays
untouched. Nothing is deleted.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))


def edit(rel, pairs):
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _ in pairs:
        assert s.count(old) == 1, "%s: %d occurrences of %r" % (rel, s.count(old), old[:70])
    for old, new in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(rel, "patched,", len(s), "bytes")


edit("lib/nav.js", [
    ("""  {
    kind: 'group',
    view: 'workers',
    label: 'Workers',
    blurb: 'What Vermonters themselves earn, and what the credential a worker holds leads to. People, not jobs.',
    items: [
      { id: 'what-people-hold', label: 'What people hold' },
      { id: 'what-people-earn', label: 'What people earn' },
    ],
  },""",
     """  // --- Hidden for now -----------------------------------------------------
  // The two panels that count people rather than jobs. components/views/Workers.js
  // and data/people.json are untouched; restore by uncommenting this block.
  // {
  //   kind: 'group',
  //   view: 'workers',
  //   label: 'Workers',
  //   blurb: 'What Vermonters themselves earn, and what the credential a worker holds leads to. People, not jobs.',
  //   items: [
  //     { id: 'what-people-hold', label: 'What people hold' },
  //     { id: 'what-people-earn', label: 'What people earn' },
  //   ],
  // },"""),
    ("""      { id: 'highest-scoring', label: 'Highest scoring' },
      { id: 'program-candidates', label: 'Program candidates' },""",
     """      { id: 'highest-scoring', label: 'Highest scoring' },
      // Hidden for now -- the screen and its four controls. The section is still
      // in Q5.js; restore by uncommenting this line.
      // { id: 'program-candidates', label: 'Program candidates' },"""),
])

# ---- the two statements that are no longer true ----------------------------
edit("components/views/About.js", [
    ("""              'Two units, and they are not interchangeable. Lightcast and OEWS count jobs and what a job asks for at entry. CPS and ACS count people and what they hold or earn. The navigation follows the distinction: every tab counts jobs except Workers, which counts people. Each panel says so again, and no chart puts a jobs figure and a people figure on the same scale.',""",
     """              'Two units, and they are not interchangeable. Lightcast and OEWS count jobs and what a job asks for at entry — including the credential a job asks for, which is not the credential the person in it holds. The Census surveys count people, and are used here only for what a county\\u2019s residents hold and earn, on the Regions map. Every chart that ranks or compares work counts jobs, each panel says which, and no chart puts a jobs figure and a people figure on the same scale.',"""),
    ("""            {
              cells: [
                'Workers',
                'What Vermonters themselves earn, and what the credential a worker holds leads to. People, not jobs',
              ],
            },""",
     ""),
    ("""              'The Overview, Wage quality, Pathways, Workers, Opportunities and Regions all carry a household selector. It moves every figure that compares pay with self-sufficiency, so set it before reading those tabs. The default is one adult with no children, which is the only household MIT publishes for every county.',""",
     """              'The Overview, Wage quality, Pathways, Opportunities and Regions all carry a household selector. It moves every figure that compares pay with self-sufficiency, so set it before reading those tabs. The default is one adult with no children, which is the only household MIT publishes for every county.',"""),
])

# ---- the register lists what the dashboard draws ---------------------------
edit("components/views/Methods.js", [
    ("""            {
              cells: [
                'Workers · What people hold',
                'What credentials employed Vermonters hold, and how that has moved since 2021',
                'CPS via IPUMS',
                'cps.json',
              ],
            },
            {
              cells: [
                'Workers · What people earn',
                'Person-level earnings against the benchmark, by the credential a worker holds',
                'ACS 1-year via IPUMS · MIT',
                'people.json',
              ],
            },""",
     ""),
    ("""            {
              cells: [
                'Opportunities · Program candidates',
                'Occupations clearing the screen, by annual openings, shaded by how much VSCS already produces for them',
                'Lightcast · IPEDS · CIP-to-SOC crosswalk',
                'lightcast.json, sow.json',
              ],
            },""",
     ""),
])
