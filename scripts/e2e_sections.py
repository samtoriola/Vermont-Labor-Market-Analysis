"""Walks every section in the sidebar and checks each one actually renders.

The cheapest test there is, and the one that catches the most: a view that
throws renders an empty section rather than an error page, so a section that
quietly stopped drawing looks exactly like one that was always empty. This opens
every group, clicks every section under it, and asserts there is a panel with a
heading and no page error behind it.

Also checks the two things the restructure is for:

  Every section carries a "how to read this" band. It is one line of orientation
  in the place the reader actually is, and a section that loses it has lost the
  only instruction it offers.

  The sidebar matches lib/nav.js. check_nav.py proves that statically against
  the source; this proves the browser agrees.

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
NAV = os.path.join(HERE, "..", "lib", "nav.js")

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)


def declared():
    """The groups and their sections, read from nav.js, commented lines dropped."""
    src = "\n".join(
        l for l in open(NAV, encoding="utf-8").read().split("\n")
        if not l.lstrip().startswith(("//", "/*", "*"))
    )
    out = []
    for m in re.finditer(r"label: '([^']+)',\s*\n\s*blurb:(.*?)(?=\n  \{|\n\];)", src, re.S):
        out.append((m.group(1), re.findall(r"\{ id: '[^']+', label: '([^']*)' \}", m.group(2))))
    return out


GROUPS = declared()
fails = []

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1100}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")

    print("%-18s %-26s %6s %6s %5s" % ("GROUP", "SECTION", "PANELS", "CHARTS", "HOWTO"))
    for group, sections in GROUPS:
        head = pg.locator(".sbgroup button, .sbitem", has_text=group).first
        if not head.count():
            fails.append("sidebar has no %r" % group)
            continue
        for label in sections:
            before = len(errs)
            item = pg.locator(".sbitem", has_text=label)
            if not item.count():
                head.click()
                pg.wait_for_timeout(200)
                item = pg.locator(".sbitem", has_text=label)
            if not item.count():
                fails.append("%s / %s: no sidebar entry" % (group, label))
                continue
            item.first.click()
            pg.wait_for_timeout(750)

            panels = pg.locator(".view .panel").count()
            charts = pg.locator(".view svg.chart, .view table").count()
            howto = pg.locator(".view .howto").count()
            print("%-18s %-26s %6d %6d %5d" % (group, label, panels, charts, howto))

            if not panels:
                fails.append("%s / %s: no panel rendered" % (group, label))
            if not charts:
                fails.append("%s / %s: neither a chart nor a table" % (group, label))
            if howto != 1:
                fails.append("%s / %s: %d how-to bands, expected 1" % (group, label, howto))
            if len(errs) > before:
                fails.append("%s / %s: %s" % (group, label, errs[before]))

            # The crumb is the only thing telling a reader which group they are
            # in once the chart fills the screen.
            crumb = " ".join(pg.locator(".crumb").first.inner_text().split())
            if group not in crumb or label not in crumb:
                fails.append("%s / %s: crumb reads %r" % (group, label, crumb))

            # Five sections are now a measure control over what used to be two
            # pages, so every option has to draw -- not just the one the section
            # opens on. The option a section opens on is the one already checked
            # above, and the rest are clicked here.
            ctl = pg.locator(".view .rankctl").first
            if ctl.count():
                opts = ctl.locator("button")
                names = [t.strip() for t in opts.all_inner_texts()]
                for i, name in enumerate(names):
                    before = len(errs)
                    opts.nth(i).click()
                    pg.wait_for_timeout(650)
                    drew = pg.locator(".view svg.chart, .view table").count()
                    if not drew:
                        fails.append("%s / %s / %s: drew nothing" % (group, label, name))
                    if len(errs) > before:
                        fails.append("%s / %s / %s: %s" % (group, label, name, errs[before]))
                print("%-18s %-26s   %s" % ("", "↳ " + str(len(names)) + " options",
                                            ", ".join(names)))

    b.close()

print("")
if errs:
    print("PAGE ERRORS: %s" % errs[:4])
print("FAIL: " + "; ".join(fails) if fails else "CLEAN — every section renders")
sys.exit(1 if fails else 0)
