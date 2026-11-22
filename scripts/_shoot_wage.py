"""Throwaway: look at the rebuilt Wage quality tab."""
import os, pathlib, sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
OUT = ROOT / "_shots"
OUT.mkdir(exist_ok=True)


def chip(pg, group, label):
    pg.locator(".rankctl", has_text=group).first.locator("button", has_text=label).first.click()
    pg.wait_for_timeout(700)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1600, "height": 1500}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem", has_text="Wage benchmark").first.click()
    pg.wait_for_timeout(1200)

    def shot(name):
        pg.locator(".view").first.screenshot(path=str(OUT / (name + ".png")))
        print("  ->", name)

    shot("w-share")
    chip(pg, "Measure", "People below")
    shot("w-count")
    chip(pg, "Rows", "Entry credential")
    shot("w-cred")
    chip(pg, "Rows", "Largest occupations")
    shot("w-occ")
    chip(pg, "Rows", "Every occupation")
    shot("w-scatter")

    pg.locator(".sbitem", has_text="County living wage").first.click()
    pg.wait_for_timeout(900)
    shot("w-county-local")
    chip(pg, "Benchmark", "One statewide floor")
    shot("w-county-state")

    # Dark, where the track has to stay distinguishable from the panel.
    pg.emulate_media(color_scheme="dark")
    pg.wait_for_timeout(500)
    shot("w-county-dark")
    pg.locator(".sbitem", has_text="Wage benchmark").first.click()
    pg.wait_for_timeout(900)
    shot("w-share-dark")
    pg.emulate_media(color_scheme="light")

    print("\n--- 390px ---")
    pg.set_viewport_size({"width": 390, "height": 1200})
    for sec in ("Wage benchmark", "County living wage"):
        pg.locator(".sbitem", has_text=sec).first.click()
        pg.wait_for_timeout(700)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        cw = pg.evaluate("document.documentElement.clientWidth")
        print("  %-24s overflow %+d" % (sec, sw - cw))
    pg.screenshot(path=str(OUT / "w-mobile.png"))

    print("\npage errors:", errs[:3] if errs else "none")
    b.close()
