"""Wire the Report tab into the navigation.

An item rather than a group: the three controls inside it are the navigation,
and splitting format and scope into sidebar sections would put the same report
behind four entries that differ only by a chip.

It sits after Regions and before About, which is where a reader arrives once
they have been through the analysis -- the tab exists to hand the analysis to
somebody who will not walk through it themselves.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

EDITS = [
    ("../lib/nav.js", [(
        """  { kind: 'item', view: 'about', label: 'About' },""",
        """  // The output tab. Everything above answers a question on screen; this one
  // packages the answers for a reader who will never open the thing.
  { kind: 'item', view: 'report', label: 'Report' },

  { kind: 'item', view: 'about', label: 'About' },""")]),

    ("../components/Dashboard.js", [
        ("""import Regions from './views/Q7';
import About from './views/About';""",
         """import Regions from './views/Q7';
import Report from './views/Report';
import About from './views/About';"""),
        ("""  alignment: Alignment,
  about: About,""",
         """  alignment: Alignment,
  report: Report,
  about: About,"""),
    ]),
]

for rel, subs in EDITS:
    p = os.path.join(H, rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _ in subs:
        if s.count(old) != 1:
            raise SystemExit("%s: %d of %r" % (rel, s.count(old), old[:60]))

for rel, subs in EDITS:
    p = os.path.join(H, rel)
    s = io.open(p, encoding="utf-8").read()
    for old, new in subs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print("patched %s" % rel)
