"""Throwaway: look at the Wage quality mockup page before it is published."""
import os, pathlib, sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = (ROOT / "_shots" / "wage-options.html").as_uri()
OUT = ROOT / "_shots"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1320, "height": 1100}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    pg.goto(PAGE, wait_until="networkidle")
    pg.wait_for_timeout(900)
    print("page errors:", errs[:4] if errs else "none")

    def shot(name, sel=None, clip=None):
        if sel:
            pg.locator(sel).first.screenshot(path=str(OUT / (name + ".png")))
        else:
            pg.screenshot(path=str(OUT / (name + ".png")), clip=clip)
        print("  ->", name)

    shot("mock-a", ".opt")
    shot("mock-b", ".opt:nth-of-type(2)")

    # the other measure on each, and the county panel both ways
    pg.locator("#a-meas button", has_text="People below").click()
    pg.wait_for_timeout(500)
    shot("mock-a-count", ".opt")
    pg.locator("#b-sort button", has_text="Share below").click()
    pg.wait_for_timeout(500)
    shot("mock-b-sorted", ".opt:nth-of-type(2)")
    pg.locator("#c-mode button", has_text="statewide").click()
    pg.wait_for_timeout(500)
    shot("mock-c-state", "section:last-of-type")
    pg.locator("#c-mode button", has_text="own floor").click()
    pg.wait_for_timeout(500)

    sect = pg.locator("section").nth(1)
    sect.screenshot(path=str(OUT / "mock-c-local.png"))
    print("  -> mock-c-local")

    pg.set_viewport_size({"width": 390, "height": 1000})
    pg.wait_for_timeout(500)
    over = pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    print("390px horizontal overflow:", over)
    b.close()
print("errors:", len(errs))
