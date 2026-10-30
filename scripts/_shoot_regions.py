"""Throwaway: look at the new county panels in both themes and at phone width."""
import os, sys, time, urllib.request, pathlib
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
OUT = pathlib.Path(__file__).resolve().parent.parent / "_shots"
OUT.mkdir(exist_ok=True)
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read(); break
    except Exception:
        time.sleep(1)

def chip(pg, group, label):
    pg.locator(".rankctl", has_text=group).first.locator("button", has_text=label).first.click()
    pg.wait_for_timeout(700)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for theme in ("light", "dark"):
        pg = b.new_context(viewport={"width": 1680, "height": 1200},
                           color_scheme=theme).new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="networkidle")
        pg.evaluate("localStorage.clear()")
        pg.reload(wait_until="networkidle")
        pg.locator(".sbitem", has_text="Counties compared").first.click()
        pg.wait_for_timeout(900)
        pg.locator(".view .panel").first.screenshot(path=str(OUT / f"cty-jobs-{theme}.png"))
        chip(pg, "Measure", "What it specialises in")
        pg.locator(".view .panel").first.screenshot(path=str(OUT / f"cty-mix-{theme}.png"))
        print(theme, "errors:", len(errs))

        if theme == "light":
            pg.set_viewport_size({"width": 390, "height": 1100})
            pg.wait_for_timeout(600)
            over = pg.evaluate("() => document.documentElement.scrollWidth - "
                               "document.documentElement.clientWidth")
            print("  390px horizontal overflow:", over)
            pg.screenshot(path=str(OUT / "cty-mix-390.png"), full_page=False)
            pg.set_viewport_size({"width": 1680, "height": 1200})
            pg.locator(".sbitem", has_text="Industry sectors").first.click()
            pg.wait_for_timeout(800)
            pg.screenshot(path=str(OUT / "howto.png"),
                          clip={"x": 0, "y": 0, "width": 1400, "height": 520})
    b.close()
print("shots in", OUT)
