"""The home page tiles, against the JSON rather than against themselves.

Four figures sit side by side on the landing page, from four different places,
and they are the first numbers anyone sees. The tiles carry no source line -- that
is in Methods' register and in workfiles/14_home_tiles.csv -- so the one thing
that can be checked here is that each tile prints what its file says, and that
the workfile register still matches the page.

Two of these count jobs, one counts people and one counts credentials. The page
cannot say so without crowding, but the workfile must, or a reader will subtract
two of them and get a number that means nothing. That is checked too.

Run against a dev or `next start` server on VT_PORT.
"""
import csv
import json
import os
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))


def D(name):
    with open(os.path.join(HERE, "..", "data", name), encoding="utf-8") as f:
        return json.load(f)


LC, SOW, GLA = D("lightcast.json"), D("sow.json"), D("glance.json")


def n(x):
    return "{:,.0f}".format(x)


# Recomputed from the JSON, so a stale tile fails rather than agreeing with itself.
WANT = [
    ("Jobs, 2025", n(LC["totalJobs"]), n(len(LC["allOcc"])) + " occupations"),
    ("Employed Vermonters", n(GLA["emp"]), str(GLA["year"])),
    ("Annual openings", n(LC["openTotal"] / LC["openYears"]), LC["window"]),
    ("VSCS completions", n(SOW["vscs"]["totalCompletions"]), "2024"),
]

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(40):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []
errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1200}).new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem", has_text="Home").first.click()
    pg.wait_for_timeout(700)

    tiles = pg.locator(".tile")
    print("--- the four tiles ---")
    if tiles.count() != len(WANT):
        fails.append("%d tiles on the home page, expected %d" % (tiles.count(), len(WANT)))

    for label, figure, detail in WANT:
        t = pg.locator(".tile", has_text=label).first
        if not t.count():
            fails.append("no tile labelled %s" % label)
            continue
        txt = " ".join(t.inner_text().split())
        ok = figure in txt and detail in txt
        print("  %-20s %-9s %s" % (label, figure, "ok" if ok else "PROBLEM"))
        if figure not in txt:
            fails.append("%s prints %r, not %s" % (label, txt[:60], figure))
        if detail not in txt:
            fails.append("%s does not say %r under the figure" % (label, detail))

    # Kept deliberately plain: a badge or a card on each of these turns the first
    # thing on the page into the busiest thing on it.
    extra = pg.locator(".tile .tcite, .tile.cited").count()
    print("  nothing else on them: %s" % ("yes" if extra == 0 else "NO, %d marks" % extra))
    if extra:
        fails.append("the tiles have picked up %d extra marks" % extra)

    b.close()

# The page cannot say which unit each figure is in, so the register has to.
print("--- 14_home_tiles.csv still matches the page ---")
with open(os.path.join(HERE, "..", "workfiles", "14_home_tiles.csv"),
          encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))
reg = {r[0]: dict(zip(rows[1], r)) for r in rows[2:] if len(r) == len(rows[1])}
for label, figure, _ in WANT:
    r = reg.get(label)
    if not r:
        fails.append("14 has no row for the %s tile" % label)
        continue
    if "{:,.0f}".format(float(r["value"])) != figure:
        fails.append("14 says %s for %s, the page says %s" % (r["value"], label, figure))
    if not r["what_it_counts"] or not r["source"] or not r["workfile_to_check"]:
        fails.append("14's %s row does not say what it counts, or where it came from" % label)
print("  %d rows, each naming a unit and a source" % len(reg))

print("")
if errs:
    print("PAGE ERRORS:", errs[:3])
print("FAIL: " + "; ".join(fails[:6]) if fails or errs else "CLEAN")
sys.exit(1 if fails or errs else 0)
