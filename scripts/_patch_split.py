"""Makes the fade check measure the visible effect rather than one attribute.

RankedBars fades a chosen-away bar with fill-opacity on its rect; RangeRows, whose
row is a line, a block and a tick rather than one rect, fades the whole row group
with opacity. Both are "this row is dimmed" on screen, and the test should be
asking that rather than naming the attribute one chart happens to use. Throwaway.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2e_split.py")
s = io.open(P, encoding="utf-8").read()

DIMMED = '''
# How many rows read as dimmed on screen, whichever way a chart does it: a faded
# fill on the bar, or a faded group around the whole row. Asking the browser for
# the effective opacity covers both and anything added later.
DIMMED_JS = """() => [...document.querySelectorAll('.split svg.chart g.bar')]
  .filter(g => {
    const rect = g.querySelector('rect:not([fill="transparent"])');
    if (rect && parseFloat(getComputedStyle(rect).fillOpacity) < 0.99) return true;
    for (let el = g; el && el.tagName !== 'svg'; el = el.parentElement) {
      if (parseFloat(getComputedStyle(el).opacity) < 0.99) return true;
    }
    return false;
  }).length"""


def dimmed(pg):
    return pg.evaluate(DIMMED_JS)

'''

anchor = "fails = []\n"
assert s.count(anchor) == 1
s = s.replace(anchor, DIMMED + "\n" + anchor)

old1 = """        faded = pg.locator('.split svg.chart rect[fill-opacity="0.32"]').count()
        if faded:
            fails.append("%s: %d bars faded with nothing chosen" % (label, faded))"""
new1 = """        faded = dimmed(pg)
        if faded:
            fails.append("%s: %d rows faded with nothing chosen" % (label, faded))"""
assert s.count(old1) == 1
s = s.replace(old1, new1)

old2 = """        # Every bar but the chosen one fades. Reference bars fade with the rest,
        # so the count is "all but one" rather than a number worth naming here.
        faded = pg.locator('.split svg.chart rect[fill-opacity="0.32"]').count()
        if faded != n_before - 1:
            fails.append(
                "%s: %d of %d bars faded, expected %d"
                % (label, faded, n_before, n_before - 1)
            )"""
new2 = """        # Every row but the chosen one fades. Reference bars fade with the rest,
        # so the count is "all but one" rather than a number worth naming here.
        faded = dimmed(pg)
        if faded != n_before - 1:
            fails.append(
                "%s: %d of %d rows faded, expected %d"
                % (label, faded, n_before, n_before - 1)
            )"""
assert s.count(old2) == 1
s = s.replace(old2, new2)

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("e2e_split.py patched,", len(s), "bytes")
