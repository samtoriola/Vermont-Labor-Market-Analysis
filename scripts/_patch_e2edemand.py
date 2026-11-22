"""e2e_demand: the per-job figure is gone from the columns, and must stay gone.

The assertion is inverted rather than deleted. A number removed from a chart
because it competed with the chart has a way of coming back, and the check that
it has not is the same cost as the check that it is there. The figure itself is
still in the table under the chart, and that is now what gets asserted.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "e2e_demand.py")
s = io.open(P, encoding="utf-8").read()

old = """            # Postings per job, on the Vermont columns only.
            notes = pg.eval_on_selector_all(
                ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")
            n_expected = sum(1 for a in expect if a["perJob"])
            if len(notes) != n_expected:
                fails.append("%s: %d per-job figures, expected %d"
                             % (tag, len(notes), n_expected))
"""
new = """            # Postings per job came off the columns in the 11/18 review: each
            # column sums to 100% and encodes no height, so the figure was
            # guarding a misreading the chart shape already prevents, and it
            # competed with the four-way split that IS the chart.
            notes = pg.eval_on_selector_all(
                ".view svg.chart text.vlab", "els => els.map(e => e.textContent)")
            if notes:
                fails.append("%s: the per-job figure is back under the columns (%d)"
                             % (tag, len(notes)))
"""

if s.count(old) != 1:
    raise SystemExit("%d occurrences" % s.count(old))
s = s.replace(old, new)

# And the figure has to still be reachable, which is the half that matters.
old2 = """            cap = " ".join(pg.locator(".view .cap").first.inner_text().split())
            if "state" not in cap.lower():
                fails.append("%s: caption does not say the denominator is stated-only" % tag)
"""
new2 = """            cap = " ".join(pg.locator(".view .cap").first.inner_text().split())
            if "state" not in cap.lower():
                fails.append("%s: caption does not say the denominator is stated-only" % tag)

            # Removed from the chart, not from the dashboard: the table under it
            # still has to carry postings per job, or the figure is simply lost.
            heads = pg.eval_on_selector_all(
                ".view table th", "els => els.map(e => e.textContent.toLowerCase())")
            if heads and not [h for h in heads if "per job" in h]:
                fails.append("%s: postings per job is not in the table either" % tag)
"""
if s.count(old2) != 1:
    raise SystemExit("%d occurrences of the caption check" % s.count(old2))
s = s.replace(old2, new2)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("e2e_demand.py patched,", len(s), "bytes")
