"""Throwaway: look at the Overview mockup before publishing it."""
import pathlib, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = (ROOT / "_shots" / "overview-options.html").as_uri()
OUT = ROOT / "_shots"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1240, "height": 1100}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    pg.goto(PAGE, wait_until="networkidle")
    pg.wait_for_timeout(800)
    for i, name in enumerate(("ov-a", "ov-b", "ov-c")):
        pg.locator(".opt").nth(i).screenshot(path=str(OUT / (name + ".png")))
        print("  ->", name)
    pg.set_viewport_size({"width": 390, "height": 1000})
    pg.wait_for_timeout(400)
    over = pg.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    print("390px horizontal overflow:", over)
    print("page errors:", errs[:3] if errs else "none")
    b.close()
