import os, sys, time, urllib.request
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = os.environ["OUTDIR"]
URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(90):
    try:
        urllib.request.urlopen(URL, timeout=3).read(); break
    except Exception: time.sleep(1)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1250}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()"); pg.reload(wait_until="networkidle")
    pg.locator(".sbitem", has_text="By credential level").first.click()
    pg.wait_for_timeout(1400)
    pg.screenshot(path=OUT + "/q4_ladder.png", full_page=True)
    print("rows:", pg.locator(".view svg.chart g.bar").count())
    print("chips:", [x.strip() for x in pg.eval_on_selector_all(
        ".view .rankctl button", "els => els.map(e => e.textContent)")])
    print("note:", " ".join(pg.locator(".view .pnote").first.inner_text().split())[:220])
    # click a rung
    pg.locator(".view svg.chart g.bar").nth(3).click()
    pg.wait_for_timeout(800)
    pane = pg.locator(".view .detail")
    print("pane:", pane.count(), "| stats:", [" ".join(x.inner_text().split())
          for x in pane.locator(".detail-stats > div").all()] if pane.count() else None)
    pg.screenshot(path=OUT + "/q4_ladder_sel.png", full_page=True)
    print("page errors:", errs[:4] if errs else 0)
    b.close()
