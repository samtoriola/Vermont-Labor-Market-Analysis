"""Throwaway: the rebuilt Overview, light and dark, desktop and phone."""
import os, pathlib, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
OUT = ROOT / "_shots"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1600, "height": 1500}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem, .navbtn", has_text="Overview").first.click()
    pg.wait_for_timeout(1200)
    pg.locator(".view").first.screenshot(path=str(OUT / "ov-live.png")); print("  -> ov-live")

    bars = pg.locator(".view svg.chart g.bar").count()
    fills = pg.evaluate("""() => { const o = {};
        document.querySelectorAll('.view svg.chart g.bar rect').forEach(r => {
          const f = getComputedStyle(r).fill; o[f] = (o[f] || 0) + 1; }); return o; }""")
    print("  bars:", bars, " distinct fills:", len(fills))
    print("  fills:", fills)
    note = " ".join(pg.locator(".view .pnote").first.inner_text().split())
    print("  read-out:", note[:200])

    pg.emulate_media(color_scheme="dark"); pg.wait_for_timeout(500)
    pg.locator(".view").first.screenshot(path=str(OUT / "ov-live-dark.png")); print("  -> ov-live-dark")
    pg.emulate_media(color_scheme="light")

    pg.set_viewport_size({"width": 390, "height": 1200}); pg.wait_for_timeout(500)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    cw = pg.evaluate("document.documentElement.clientWidth")
    print("  390px overflow: %+d" % (sw - cw))
    print("  page errors:", errs[:3] if errs else "none")
    b.close()
