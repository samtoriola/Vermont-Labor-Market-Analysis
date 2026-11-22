"""Throwaway: the Overview's click-through, pane then full table."""
import os, pathlib, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
OUT = ROOT / "_shots"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1400}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem, .navbtn", has_text="Overview").first.click()
    pg.wait_for_timeout(1100)

    w0 = pg.locator(".view svg.chart").first.get_attribute("viewBox")
    print("  chart viewBox, nothing selected:", w0)

    pg.locator(".view svg.chart g.bar").nth(2).click()   # Food Preparation
    pg.wait_for_timeout(700)
    pane = pg.locator(".view .detail")
    print("  pane open:", pane.count() > 0)
    if pane.count():
        print("  pane label :", pane.locator(".dlabel").inner_text().strip())
        print("  pane title :", pane.locator("h4").inner_text().strip())
        stats = [" ".join(s.inner_text().split()) for s in pane.locator(".detail-stats > div").all()]
        print("  pane stats :", " | ".join(stats))
        print("  rows shown :", pane.locator("tbody tr").count())
        print("  more link  :", pane.locator(".morelink").inner_text().strip())
    print("  chart viewBox, pane open:", pg.locator(".view svg.chart").first.get_attribute("viewBox"))
    fills = pg.evaluate("""() => [...document.querySelectorAll('.view svg.chart g.bar rect')]
        .map(r => getComputedStyle(r).fillOpacity)""")
    print("  distinct fill-opacities with a bar chosen:", sorted(set(fills)))
    pg.locator(".view").first.screenshot(path=str(OUT / "ov-split.png")); print("  -> ov-split")

    pane.locator(".morelink").click()
    pg.wait_for_timeout(800)
    dr = pg.locator(".drill")
    print("  drill open :", dr.count() > 0)
    if dr.count():
        print("  drill title:", dr.locator("h3").inner_text().strip())
        print("  drill rows :", dr.locator("tbody tr").count())
        print("  search+filter:", dr.locator(".dtsearch").count() > 0 and dr.locator(".dtfilter select").count() > 0)
        stats = [" ".join(s.inner_text().split()) for s in dr.locator(".dstat").all()]
        print("  drill stats:", " | ".join(stats))
    pg.screenshot(path=str(OUT / "ov-drill.png")); print("  -> ov-drill")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(400)

    pg.set_viewport_size({"width": 390, "height": 1200}); pg.wait_for_timeout(500)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    cw = pg.evaluate("document.documentElement.clientWidth")
    print("  390px overflow: %+d" % (sw - cw))
    print("  page errors:", errs[:3] if errs else "none")
    b.close()
