import os, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(H, "..", "_shots", "pathways-options.html"))
OUT = os.environ.get("OUTDIR", os.path.join(H, "..", "_shots"))
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1340, "height": 1100}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("file:///" + SRC.replace("\\", "/"), wait_until="networkidle")
    pg.wait_for_timeout(900)
    pg.screenshot(path=os.path.join(OUT, "path_full.png"), full_page=True)
    wide = pg.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1")
    print("horizontal page scroll:", wide)
    print("console/page errors:", errs[:3] if errs else 0)
    pg.set_viewport_size({"width": 390, "height": 900})
    pg.wait_for_timeout(500)
    wide_m = pg.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1")
    print("horizontal page scroll at 390px:", wide_m)
    pg.screenshot(path=os.path.join(OUT, "path_mobile.png"))
    b.close()
