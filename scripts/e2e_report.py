"""The Report tab: the output agrees with the tabs it came from.

A report travels away from the dashboard, so the thing that matters is not that
it renders but that it cannot print a figure the tool would contradict. Two of
these checks exist because the first build did exactly that:

  openings a year   48,718 printed against the home page's 48,893, because
                    summing the 22 occupation groups drops the occupations that
                    carry no group
  share below       42.5% printed against Wage quality's 41.1%, because rolling
                    the five credential tiers up is not the same arithmetic as
                    reading every occupation's pay ladder

Both are recomputed here from data/ and compared with what the page prints.

Also checked: every scope builds (all 14 counties, all 22 groups, a sample of
programs), both formats render, the benchmark moves the figures, the caveats
reach the output, and the rendered text carries none of the words
check_report_language.py bans -- that check reads the source, this one reads
what a person would actually see, which includes anything arriving from data.

Run against a dev or `next start` server on VT_PORT.
"""
import json
import os
import re
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda n: json.load(open(os.path.join(HERE, "..", "data", n), encoding="utf-8"))
LC = D("lightcast.json")
PCT = D("percentiles.json")
SOW = D("sow.json")
CTY = D("counties.json")

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

fails = []

# ---- the arithmetic the page has to match, computed here independently -----

PTS = [(10, "p10"), (25, "p25"), (50, "p50"), (75, "p75"), (90, "p90")]


def share_below(box, floor):
    if not box:
        return None
    xs = [(box[k], q) for q, k in PTS if box.get(k)]
    if len(xs) < 2:
        return None
    if floor <= xs[0][0]:
        return 0.0
    if floor >= xs[-1][0]:
        return 100.0
    for i in range(len(xs) - 1):
        v0, q0 = xs[i]
        v1, q1 = xs[i + 1]
        if v0 <= floor <= v1:
            t = 0 if v1 == v0 else (floor - v0) / (v1 - v0)
            return q0 + t * (q1 - q0)
    return None


def state_below(lw_key):
    floor = LC["livingWage"][lw_key] * LC["hours"]
    tot = 0.0
    bel = 0.0
    for o in LC["allOcc"]:
        s = share_below(PCT["occ"].get(o.get("s")), floor)
        if s is None:
            continue
        j = o.get("j") or 0.0
        tot += j
        bel += j * s / 100
    return 100 * bel / tot if tot else None


OPEN = LC["openTotal"] / LC["openYears"]
# Net change, which is what the page used to print, and gross -- the jobs added
# over the occupations the projection puts up, which is what it prints now.
ADDED = sum((o.get("g5") or 0) for o in LC["allOcc"]) / 5
GROSS = sum(max(o.get("g5") or 0, 0) for o in LC["allOcc"]) / 5
BELOW_DEFAULT = state_below(LC["defaultLW"])

print("expected: openings %s/yr, added %s/yr gross (%s/yr net), below %.1f%%"
      % ("{:,.0f}".format(OPEN), "{:,.0f}".format(GROSS),
         "{:,.0f}".format(ADDED), BELOW_DEFAULT))

# Words the output must not contain, mirroring check_report_language.py.
BANNED = ["best", "worst", "poor", "problem", "crisis", "failing", "underpaid",
          "healthy", "struggling", "alarming", "troubling", "should", "must",
          "simply", "clearly", "obviously", "vulnerable", "mismatch"]


def chips(pg, group):
    return pg.locator(".rankctl", has_text=group).locator("button")


def pick_chip(pg, group, label):
    chips(pg, group).filter(has_text=re.compile("^%s$" % re.escape(label))).first.click()
    pg.wait_for_timeout(700)


def out_text(pg):
    return " ".join(pg.locator("#rpt-out").inner_text().split())


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1400}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(600)
    pg.locator(".sbitem", has_text="Report").first.click()
    pg.wait_for_timeout(1400)

    if not pg.locator("#rpt-out").count():
        fails.append("the report output did not render at all")
        print("FAIL  no #rpt-out")
        b.close()
        sys.exit(1)

    # ---- 1. the two figures that disagreed with the tabs on the first build
    txt = out_text(pg)
    want_open = "{:,.0f}".format(OPEN)
    want_below = "%.1f%%" % BELOW_DEFAULT
    print("\n--- Vermont / one-pager ---")
    print("  openings printed as %s (home page prints %s)"
          % ("found" if want_open in txt else "MISSING", want_open))
    if want_open not in txt:
        fails.append("openings a year: %s is not in the output (the home page prints it)" % want_open)
    if want_below not in txt:
        fails.append("share below: %s is not in the output (Wage quality prints it)" % want_below)
    else:
        print("  share below printed as %s, matching Wage quality" % want_below)

    # The number of findings should match what the control bar claims.
    n_fnd = pg.locator("#rpt-out .rfnd").count()
    claim = pg.locator(".rptgo .ctrlnote").inner_text()
    m = re.search(r"(\d+) findings", claim)
    if not m or int(m.group(1)) != n_fnd:
        fails.append("control bar says %r but the page has %d findings" % (claim, n_fnd))
    print("  %d findings rendered, control bar agrees" % n_fnd)

    # Every finding needs a figure the reader can check, not just a headline.
    thin = []
    for i in range(n_fnd):
        f = pg.locator("#rpt-out .rfnd").nth(i)
        has = f.locator(".rbar").count() + f.locator(".rtbl tr").count() + f.locator(".rstat").count()
        if not has:
            thin.append(f.locator("h4").inner_text()[:50])
        if not f.locator(".rsrc").count():
            fails.append("a finding carries no source line: %s" % f.locator("h4").inner_text()[:50])
    if thin:
        fails.append("findings with no figures under them: %s" % thin)

    # Caveats travel with the output.
    for key in ["jobs, not people", "modelled", "pay distribution"]:
        if key.lower() not in txt.lower():
            fails.append("the one-pager does not carry the caveat about %r" % key)

    # ---- 2. the benchmark actually moves the figures
    sel = pg.locator("#lw-select")
    sel.select_option(value="1 adult, 1 child")
    pg.wait_for_timeout(900)
    txt2 = out_text(pg)
    want2 = "%.1f%%" % state_below("1 adult, 1 child")
    if want2 not in txt2:
        fails.append("after switching benchmark, %s is not in the output" % want2)
    else:
        print("  benchmark switch moves the share to %s" % want2)
    if txt2 == txt:
        fails.append("switching the benchmark changed nothing in the output")
    sel.select_option(value=LC["defaultLW"])
    pg.wait_for_timeout(800)

    # ---- 3. the deck renders, and prints every slide rather than one
    pick_chip(pg, "Format", "Slide deck")
    n_sl = pg.locator("#rpt-out .rslide").count()
    shown = pg.locator("#rpt-out .rslide:not(.off)").count()
    print("\n--- Vermont / slide deck ---")
    print("  %d slides in the DOM, %d visible" % (n_sl, shown))
    if n_sl != n_fnd + 2:
        fails.append("%d slides for %d findings; expected %d" % (n_sl, n_fnd, n_fnd + 2))
    if shown != 1:
        fails.append("%d slides visible at once; the viewer should show one" % shown)
    # All of them have to be in the document, or printing yields a one-slide deck.
    if n_sl < 3:
        fails.append("the deck has fewer than three slides")
    pg.locator(".rdots .rdot").nth(2).click()
    pg.wait_for_timeout(500)
    if pg.locator("#rpt-out .rslide:not(.off)").count() != 1:
        fails.append("after paging, the deck does not show exactly one slide")

    # ---- 3b. no slide silently drops a row ----------------------------
    # The frame is fixed 16:9 and clips rather than scrolls, so content that
    # does not fit simply disappears -- at its worst a source line reading
    # "five highest replacement rates, and the lowest" sat above four rows.
    # Measured with rectangles, not scrollHeight: the fit box is scaled with a
    # transform, which layout metrics do not see.
    CLIP = """() => {
      const s = document.querySelector('.rslide:not(.off)');
      const bdy = s.querySelector('.rbody');
      if (!bdy) return { over: 0, head: '' };
      const inner = bdy.firstElementChild;
      const br = bdy.getBoundingClientRect();
      let bottom = br.top;
      Array.from(inner ? inner.children : []).forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.height) bottom = Math.max(bottom, r.bottom);
      });
      return { over: Math.round(bottom - br.bottom),
               head: s.querySelector('h3').textContent.slice(0, 44) };
    }"""

    def clip_scan(tag):
        n = pg.locator(".rdots .rdot").count()
        worst = []
        for i in range(n):
            pg.locator(".rdots .rdot").nth(i).click()
            pg.wait_for_timeout(190)
            o = pg.evaluate(CLIP)
            # Up to 6px is the last row's own border, not a dropped row.
            if o["over"] > 6:
                worst.append((i + 1, o["over"], o["head"]))
        print("  %-22s %d slides, clipped: %s" % (tag, n, worst or "none"))
        if worst:
            fails.append("%s: slides clip their content: %s" % (tag, worst))
        return n

    print()
    pick_chip(pg, "Format", "Slide deck")
    clip_scan("Vermont")

    # ---- 4. every scope builds
    print("\n--- every scope ---")
    for group, label, sel_id, n_expect in [
        ("Scope", "A county", "#rpt-pick", 14),
        ("Scope", "An occupation group", "#rpt-pick", 22),
        ("Scope", "A VSCS program", "#rpt-pick", None),
    ]:
        pick_chip(pg, group, label)
        pick_chip(pg, "Format", "One-pager")
        opts = pg.locator(sel_id + " option")
        n = opts.count()
        if n_expect and n != n_expect:
            fails.append("%s offers %d options, expected %d" % (label, n, n_expect))
        print("  %-22s %d options" % (label, n))
        # Walk a sample rather than all 149 programs: first, middle, last.
        idx = sorted({0, n // 2, n - 1})
        for i in idx:
            val = opts.nth(i).get_attribute("value")
            pg.locator(sel_id).select_option(value=val)
            pg.wait_for_timeout(450)
            k = pg.locator("#rpt-out .rfnd").count()
            t = out_text(pg)
            if k == 0:
                fails.append("%s = %r produced no findings" % (label, val))
            if "NaN" in t or "undefined" in t or "—%" in t:
                fails.append("%s = %r prints a broken figure" % (label, val))
            bad = [w for w in BANNED if re.search(r"(?<![a-z])%s(?![a-z])" % w, t.lower())]
            if bad:
                fails.append("%s = %r prints a word that grades: %s" % (label, val, bad))
        print("    sampled %d of them, all built" % len(idx))
        # The deck for this scope, on the option left selected above.
        pick_chip(pg, "Format", "Slide deck")
        clip_scan(label)
        pick_chip(pg, "Format", "One-pager")

    # ---- 4a. claims match the data, and both ends survive a trim ------
    # The headline on the replacement finding used to read "groups with higher
    # replacement rates have smaller shares clearing the benchmark", which
    # states a rule the data does not carry: at r = -0.71 roughly four ordered
    # pairs in five run that way, and the group with the fifth-highest
    # replacement rate clears 85.8%. It now counts the run at the top, which is
    # checkable -- so it is checked, against the same data the tab reads.
    pick_chip(pg, "Scope", "Vermont")
    pick_chip(pg, "Format", "One-pager")

    fams = [r for r in LC["families"]
            if r.get("turn") is not None and r.get("above")]
    fams.sort(key=lambda r: -r["turn"])
    clear = lambda r: r["above"][LC["defaultLW"]]
    state_clear = 100 - BELOW_DEFAULT
    run = 0
    while run < len(fams) and clear(fams[run]) < state_clear:
        run += 1
    import math
    top_max = math.ceil(max(clear(r) for r in fams[:run]))
    lowest_turn = fams[-1]["f"]

    found = pg.evaluate("""() => Array.from(document.querySelectorAll('.rfnd')).map((f) => ({
        head: f.querySelector('h4').textContent.replace(/\s+/g, ' ').trim(),
        src: (f.querySelector('.rsrc') || {}).textContent || '',
        last: (() => { const rs = f.querySelectorAll('tbody tr');
          return rs.length ? rs[rs.length - 1].querySelector('td').textContent.trim() : null; })(),
      }))""")

    rep = [f for f in found if "replacement rates" in f["head"]]
    if not rep:
        fails.append("the replacement finding is not on the one-pager")
    else:
        h = rep[0]["head"]
        print()
        print("  headline: %s" % h[2:])
        if ("%d highest" % run) not in h or ("%d%%" % top_max) not in h:
            fails.append("the headline says %r; the data says a run of %d under %d%%"
                         % (h, run, top_max))
        if rep[0]["last"] != lowest_turn:
            fails.append("the trimmed table ends on %r; the lowest replacement rate is %r"
                         % (rep[0]["last"], lowest_turn))
        else:
            print("  table still ends on %s, the lowest replacement rate" % lowest_turn)

    # Any table whose source line promises both ends has to show both ends.
    # Bars carry the same promise in their own note, which reads "showing 5 of
    # 14, including both ends" with no "rows" in it -- so match on the row
    # wording, or every bar chart looks like a table with no rows.
    thin = {r["f"] for r in SOW["vscs"]["byFamily"] if r["linked"] < 1}
    for f in found:
        if "rows, including both ends" in f["src"] and f["last"] is None:
            fails.append("a finding promises both table ends with no table: %s"
                         % f["head"][:50])
    vscs = [f for f in found if "Attributed graduates" in f["head"]]
    if vscs and vscs[0]["last"] not in thin:
        fails.append("the VSCS table ends on %r, which is not one of the groups "
                     "under one attributed graduate" % vscs[0]["last"])
    elif vscs:
        print("  VSCS table still ends on %s, a group under one graduate" % vscs[0]["last"])

    # ---- 4b. the headlines that state a shape, at every benchmark ----
    # Five more claims went the way the replacement one did, and four of them
    # were wrong at a benchmark that is not the default:
    #
    #   credential ladder   "rises with the credential the work asks for" --
    #                       it falls at a rung at three of the eight, and is
    #                       flat at 100% at two more
    #   openings split      counted NET job change as "jobs the projection
    #                       creates", netting 171 shrinking occupations against
    #                       the rest
    #   group geography     "where the group is a larger share of local jobs"
    #                       over the six highest local shares, which for nine
    #                       of the 22 groups included counties below the state
    #   county mix          named the group that differs most from the state
    #                       without putting it in the table, in 5 of 14
    #   replacement run     run = 0 at the two-earner benchmark printed
    #                       "under -Infinity% of jobs"
    #
    # So the shape is recomputed here and the headline has to match it.
    print("\n--- headlines that state a shape ---")

    TIERS = ["No formal credential", "High school", "Sub-baccalaureate",
             "Bachelor's", "Graduate / professional"]
    trow = {t["t"]: t for t in LC["tiers"]}
    seen = {"rises": 0, "spans": 0, "same": 0}
    for key in LC["livingWage"]:
        pg.locator("#lw-select").select_option(value=key)
        pg.wait_for_timeout(620)
        heads = pg.eval_on_selector_all(
            "#rpt-out .rfnd h4",
            "e => e.map(x => x.textContent.replace(/\\s+/g, ' ').trim())")
        lad = [h for h in heads
               if "clear" in h.lower() and ("credential" in h.lower() or "rung" in h.lower())]
        vals = [trow[t]["above"][key] for t in TIERS if t in trow]
        mono = all(b >= a - 0.05 for a, b in zip(vals, vals[1:]))
        flat = max(vals) - min(vals) < 0.05
        if not lad:
            fails.append("no credential-ladder headline at %r" % key)
        else:
            h = lad[0]
            if flat:
                ok, seen["same"] = "same share" in h, seen["same"] + 1
            elif mono:
                ok, seen["rises"] = "rises at every rung" in h, seen["rises"] + 1
            else:
                ok, seen["spans"] = ("spans" in h and "rises" not in h), seen["spans"] + 1
            if not ok:
                fails.append("at %r the ladder is %s, and the headline reads %r"
                             % (key, "flat" if flat else "rising" if mono
                                else "not monotonic", h))
        # Nothing anywhere in the output may print a non-finite figure.
        t_k = out_text(pg)
        for junk in ["Infinity", "NaN", "undefined"]:
            if junk in t_k:
                fails.append("at %r the report prints %r" % (key, junk))
    print("  credential ladder: %d rising, %d spanning, %d flat, over %d benchmarks"
          % (seen["rises"], seen["spans"], seen["same"], len(LC["livingWage"])))
    pg.locator("#lw-select").select_option(value=LC["defaultLW"])
    pg.wait_for_timeout(650)

    # Growth openings are the jobs ADDED, over the occupations the projection
    # puts up. Netting the ones it puts down against them understated the added
    # side by 12% and put the ratio at 22.7 refills per added job, not 19.8.
    t = out_text(pg)
    if "{:,}".format(round(GROSS)) not in t:
        fails.append("the openings split does not print %s, the jobs added a year"
                     % "{:,}".format(round(GROSS)))
    elif ("%.1f" % round((OPEN - GROSS) / GROSS, 1)) not in t:
        fails.append("the openings split does not print the ratio %.1f"
                     % round((OPEN - GROSS) / GROSS, 1))
    else:
        print("  openings split: %s added a year, %.1f refilled per added job"
              % ("{:,}".format(round(GROSS)), (OPEN - GROSS) / GROSS))

    # The group a reading names has to have a row under it.
    pick_chip(pg, "Scope", "A county")
    opts = pg.locator("#rpt-pick option")
    missing = []
    for i in range(opts.count()):
        pg.locator("#rpt-pick").select_option(value=opts.nth(i).get_attribute("value"))
        pg.wait_for_timeout(380)
        got = pg.evaluate("""() => {
          const f = Array.from(document.querySelectorAll('.rfnd')).filter(
            (x) => /Occupation mix/.test(x.querySelector('h4').textContent))[0];
          if (!f) return null;
          return { read: (f.querySelector('.rread') || {}).textContent || '',
                   rows: Array.from(f.querySelectorAll('tbody tr td:first-child'))
                          .map((td) => td.textContent.trim()) };
        }""")
        if not got:
            continue
        named = got["read"].split(" differs most")[0].strip()
        if named and named not in got["rows"]:
            missing.append(named)
    if missing:
        fails.append("the mix reading names a group with no row beneath it: %s" % missing)
    else:
        print("  occupation mix: the group named as differing most has a row in all "
              "%d counties" % opts.count())

    # And the geography bars carry the statewide share, so the comparison the
    # headline used to assert is on the page instead.
    pick_chip(pg, "Scope", "An occupation group")
    gopts = pg.locator("#rpt-pick option")
    vals = [gopts.nth(i).get_attribute("value") for i in range(gopts.count())]
    for val in [v for v in vals if "Healthcare Support" in (v or "")] or vals[:1]:
        pg.locator("#rpt-pick").select_option(value=val)
        pg.wait_for_timeout(520)
        got = pg.evaluate("""() => {
          const f = Array.from(document.querySelectorAll('.rfnd')).filter(
            (x) => /counties/.test(x.querySelector('h4').textContent))[0];
          if (!f) return null;
          return { head: f.querySelector('h4').textContent,
                   bars: Array.from(f.querySelectorAll('.rbl')).map((b) => b.textContent) };
        }""")
        if not got:
            fails.append("%s carries no geography finding" % val)
        elif "larger share" in got["head"]:
            fails.append("%s still claims its counties hold a larger share" % val)
        elif not [b for b in got["bars"] if "Vermont" in b]:
            fails.append("%s: the geography bars carry no statewide row to compare "
                         "against" % val)
        else:
            print("  %s: the bars carry the statewide share" % val)
    pick_chip(pg, "Scope", "Vermont")

    # ---- 4c. the one-pager is one page -------------------------------
    # The name is a promise, and it is the promise that breaks quietly: adding
    # a finding, or a county whose name wraps a headline, costs a line and the
    # document silently becomes two pages. Counted from a real PDF rather than
    # from element heights, because the panel's own chrome printing above the
    # report is what made it five pages the first time and no element
    # measurement of the report itself would have shown that.
    print()
    pick_chip(pg, "Format", "One-pager")
    for label in ["Vermont", "A county", "An occupation group", "A VSCS program"]:
        pick_chip(pg, "Scope", label)
        pdf = pg.pdf(format="Letter", print_background=True,
                     margin={"top": "0.5in", "bottom": "0.5in",
                             "left": "0.5in", "right": "0.5in"})
        n = len(re.findall(rb"/Type\s*/Page[^s]", pdf))
        print("  one-pager / %-22s %d page(s)" % (label, n))
        if n != 1:
            fails.append("the one-pager prints %d pages for %s" % (n, label))

    # The deck is the opposite promise: every slide on its own page, not just
    # the one the viewer happens to be showing.
    pick_chip(pg, "Scope", "Vermont")
    pick_chip(pg, "Format", "Slide deck")
    want = pg.locator("#rpt-out .rslide").count()
    pdf = pg.pdf(format="Letter", print_background=True,
                 margin={"top": "0.5in", "bottom": "0.5in",
                         "left": "0.5in", "right": "0.5in"})
    n = len(re.findall(rb"/Type\s*/Page[^s]", pdf))
    print("  deck / Vermont             %d page(s) for %d slides" % (n, want))
    if n != want:
        fails.append("the deck prints %d pages for %d slides" % (n, want))
    pick_chip(pg, "Format", "One-pager")

    # ---- 5. back to Vermont, and the rendered text stays clean
    pick_chip(pg, "Scope", "Vermont")
    t = out_text(pg)
    bad = [w for w in BANNED if re.search(r"(?<![a-z])%s(?![a-z])" % w, t.lower())]
    if bad:
        fails.append("the Vermont report prints a word that grades: %s" % bad)
    else:
        print("\n  rendered text carries none of the %d banned terms" % len(BANNED))

    if errs:
        fails.append("page errors: %s" % errs[:2])
    b.close()

print()
if fails:
    for f in fails:
        print("FAIL  %s" % f)
    sys.exit(1)
print("OK  the report agrees with the tabs it came from")
