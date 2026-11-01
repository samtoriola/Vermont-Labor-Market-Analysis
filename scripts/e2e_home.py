"""The home page tiles, and the sources they now carry.

Four figures sit side by side on the landing page and come from four different
places. Two of them count jobs, one counts people and one counts credentials, so
a reader who assumes one universe will subtract two of them and get a number that
means nothing. The source is on hover, which is only useful if it is actually
there and actually says the right thing -- a tooltip that silently stops firing
looks exactly like a tile with no source, and nobody files a bug about a thing
they never knew existed.

So this hovers each tile and reads the card: the source name, the vintage, the
file the app imports and the workfile that reproduces the figure, every one of
them checked against data/ rather than against the page. It also checks the
keyboard path, because a hover-only source is no source for anyone navigating by
tab, and that the workfile each card names is on disk.

Run against a dev or `next start` server on VT_PORT.
"""
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


# What each tile must print, and what its card must say. Figures come from the
# JSON, not from the page, so a stale tile fails rather than agreeing with itself.
WANT = [
    {
        "label": "Jobs, 2025",
        "figure": n(LC["totalJobs"]),
        "says": ["Vermont occupation data", "2025", "lightcast.json",
                 "01_occupations_master.csv", n(sum(o.get("j") or 0 for o in LC["allOcc"]))],
        "unit": "not people",
        "workfile": "01_occupations_master.csv",
    },
    {
        "label": "Employed Vermonters",
        "figure": n(GLA["emp"]),
        "says": ["Census household survey", str(GLA["year"]), "glance.json",
                 "15_labor_force_cps.csv", n(GLA["nPeopleLf"])],
        "unit": "survey estimate",
        "workfile": "15_labor_force_cps.csv",
    },
    {
        "label": "Annual openings",
        "figure": n(LC["openTotal"] / LC["openYears"]),
        "says": ["Vermont occupation data", LC["window"], "lightcast.json",
                 "00_headline_figures.csv", n(LC["openTotal"])],
        "unit": "replacing people who leave",
        "workfile": "00_headline_figures.csv",
    },
    {
        "label": "VSCS completions",
        "figure": n(SOW["vscs"]["totalCompletions"]),
        "says": ["Federal completions data", "2024", "sow.json",
                 "10_vscs_production.csv", "Vermont State University"],
        "unit": "not people",
        "workfile": "10_vscs_production.csv",
    },
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
    print("  %d tiles, %d cited" % (tiles.count(), pg.locator(".tile.cited").count()))
    if tiles.count() != len(WANT):
        fails.append("%d tiles on the home page, expected %d" % (tiles.count(), len(WANT)))
    if pg.locator(".tile.cited .tcite").count() != len(WANT):
        fails.append("not every tile carries the badge that says it has a source")

    for w in WANT:
        t = pg.locator(".tile", has_text=w["label"]).first
        if not t.count():
            fails.append("no tile labelled %s" % w["label"])
            continue
        txt = " ".join(t.inner_text().split())
        if w["figure"] not in txt:
            fails.append("%s prints %r, not %s" % (w["label"], txt[:60], w["figure"]))

        t.hover()
        pg.wait_for_timeout(260)
        card = " ".join(pg.locator("#tip").inner_text().split())
        missing = [x for x in w["says"] + [w["unit"]] if x not in card]
        shown = pg.evaluate("getComputedStyle(document.getElementById('tip')).opacity") == "1"
        print("  %-20s %-9s card: %s"
              % (w["label"], w["figure"], "ok" if shown and not missing else "PROBLEM"))
        if not shown:
            fails.append("hovering %s showed no card" % w["label"])
        if missing:
            fails.append("%s's card does not say: %s" % (w["label"], ", ".join(missing)))
        if w["label"] not in card:
            fails.append("%s's card is not titled with the tile" % w["label"])

        pg.mouse.move(4, 4)
        pg.wait_for_timeout(200)
        if pg.evaluate("getComputedStyle(document.getElementById('tip')).opacity") == "1":
            fails.append("%s's card stayed up after the pointer left" % w["label"])

        p = os.path.join(HERE, "..", "workfiles", w["workfile"])
        if not os.path.exists(p):
            fails.append("%s's card names %s, which is not in workfiles/"
                         % (w["label"], w["workfile"]))

    # A source only on hover is no source for anyone moving by keyboard.
    print("--- the keyboard path ---")
    pg.locator(".tile.cited").first.focus()
    pg.wait_for_timeout(260)
    kb = " ".join(pg.locator("#tip").inner_text().split())
    ok = pg.evaluate("getComputedStyle(document.getElementById('tip')).opacity") == "1"
    print("  focusing a tile shows its card: %s" % ("yes" if ok and "Source" in kb else "NO"))
    if not ok or "Source" not in kb:
        fails.append("focusing a tile does not show its source")

    # The second tile counts people and the others count jobs. If that ever stops
    # being said, the page invites a subtraction that means nothing.
    people = pg.locator(".tile", has_text="Employed Vermonters").first
    people.hover()
    pg.wait_for_timeout(240)
    card = " ".join(pg.locator("#tip").inner_text().split())
    if "People" not in card:
        fails.append("the employed-Vermonters card no longer says it counts people")

    b.close()

print("")
if errs:
    print("PAGE ERRORS:", errs[:3])
print("FAIL: " + "; ".join(fails[:6]) if fails or errs else "CLEAN")
sys.exit(1 if fails or errs else 0)
