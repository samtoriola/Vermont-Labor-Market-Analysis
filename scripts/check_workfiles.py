"""Checks the workfiles against each other and against the dashboard.

The workfiles exist so a figure can be verified by hand, which only helps if the
chain actually closes: the per-occupation rows in 01 have to sum to the per-group
rows in 02, those have to sum to the headline in 00, and the headline has to be
the number on screen. Any one of those can come apart on a stale rebuild without
a single file looking wrong on its own.

So this walks the chain the README tells a reader to walk, then opens the
dashboard and checks the headline figures are the ones it prints.

    VT_PORT=3205 python check_workfiles.py
"""
import csv
import io
import os
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(HERE, "..", "workfiles")
fails = []


def read(name):
    """Rows as dicts. The first line is a provenance comment, not a header."""
    with io.open(os.path.join(WF, name), encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    head = rows[1]
    return [dict(zip(head, r)) for r in rows[2:] if len(r) == len(head)]


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def close(a, b, tol, what):
    if a is None or b is None:
        fails.append("%s: missing a figure (%s, %s)" % (what, a, b))
    elif abs(a - b) > tol:
        fails.append("%s: %.3f against %.3f" % (what, a, b))
    return abs((a or 0) - (b or 0)) <= tol


occ = read("01_occupations_master.csv")
grp = read("02_overview_and_wage_by_group.csv")
lad = read("03_pathways_credential_ladder.csv")
vscs = read("09_vscs_alignment_by_group.csv")
head = {r["figure"]: num(r["value"]) for r in read("00_headline_figures.csv")}

print("--- 01 sums to 02 ---")
by_group = {}
for o in occ:
    if o["has_pay_ladder"] != "yes":
        continue
    g = by_group.setdefault(o["occupation_group"], [0.0, 0.0, 0])
    g[0] += num(o["jobs_2025"]) or 0
    g[1] += num(o["jobs_below_benchmark"]) or 0
    g[2] += 1
off = 0
for r in grp:
    mine = by_group.get(r["occupation_group"])
    if not mine:
        fails.append("02 has %s, which is in no row of 01" % r["occupation_group"])
        continue
    if abs(mine[0] - (num(r["jobs_priced"]) or 0)) > 1:
        off += 1
        fails.append("%s: 01 sums to %.1f jobs, 02 says %s"
                     % (r["occupation_group"], mine[0], r["jobs_priced"]))
    if abs(mine[1] - (num(r["jobs_below_benchmark"]) or 0)) > 1:
        off += 1
        fails.append("%s: 01 sums to %.1f below, 02 says %s"
                     % (r["occupation_group"], mine[1], r["jobs_below_benchmark"]))
print("  %d groups, %d disagreements" % (len(grp), off))

print("--- 02 sums to 00 ---")
jobs = sum(num(r["jobs_priced"]) or 0 for r in grp)
below = sum(num(r["jobs_below_benchmark"]) or 0 for r in grp)
close(jobs, head["Jobs with a published pay ladder"], 1, "priced jobs")
close(below / jobs * 100, head["Share of priced jobs below it"], 0.05, "share below")
print("  %s priced jobs, %.1f%% below the benchmark" % ("{:,.0f}".format(jobs), below / jobs * 100))

print("--- 03 carries the pooled ladder, not the published one ---")
hs = [r for r in lad if r["entry_credential"] == "High school"]
if not hs:
    fails.append("03 has no high-school row")
else:
    close(num(hs[0]["pooled_p50"]), head["Midpoint high-school job"], 1, "pooled midpoint")
    pooled, pub = num(hs[0]["pooled_p50"]), num(hs[0]["published_p50"])
    print("  high school: pooled %s, published %s" % (pooled, pub))
    if pooled is not None and pub is not None and abs(pooled - pub) < 100:
        fails.append("03's pooled and published midpoints agree — one of them is wrong")

print("--- 09 sums to 00 ---")
g = sum(num(r["graduates_attributed"]) or 0 for r in vscs)
o = sum(num(r["openings_asking_for_a_vscs_credential"]) or 0 for r in vscs)
close(g, head["Completions landing in a Vermont occupation"], 1, "graduates attributed")
close(o, head["Openings asking for a VSCS credential"], 1, "credential-requiring openings")
close(g / o * 100, head["Graduates vs openings that ask"], 0.05, "graduates vs openings")
print("  %.0f graduates against %s openings = %.1f%%" % (g, "{:,.0f}".format(o), g / o * 100))

# ---- and the headline figures are what the dashboard prints ----------------
URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
try:
    for _ in range(30):
        try:
            urllib.request.urlopen(URL, timeout=3).read()
            break
        except Exception:
            time.sleep(1)
    from playwright.sync_api import sync_playwright
except Exception:
    print("\n--- the dashboard --- playwright not available, skipped")
else:
    print("--- the dashboard prints them ---")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1300}).new_page()
        pg.goto(URL, wait_until="networkidle")
        pg.evaluate("localStorage.clear()")
        pg.reload(wait_until="networkidle")
        want = [
            ("Overview", "{:,.0f}".format(head["Jobs with a published pay ladder"]),
             "jobs with a published pay ladder"),
            ("By credential level", "${:,.0f}".format(head["Midpoint high-school job"]),
             "the midpoint high-school job"),
            ("Against demand", "{:,.0f}".format(head["Openings asking for a VSCS credential"]),
             "openings asking for a VSCS credential"),
        ]
        for section, figure, what in want:
            pg.locator(".sbitem, .navbtn", has_text=section).first.click()
            pg.wait_for_timeout(1300)
            txt = " ".join(pg.locator(".view").inner_text().split())
            ok = figure in txt
            print("  %-22s %-12s %s" % (section, figure, "found" if ok else "NOT ON THE PAGE"))
            if not ok:
                fails.append("%s is %s in the workfiles and not on %s" % (what, figure, section))
        b.close()

print("")
print("FAIL: " + "; ".join(fails[:6]) if fails else "CLEAN — the workfiles agree with each other and with the dashboard")
sys.exit(1 if fails else 0)
