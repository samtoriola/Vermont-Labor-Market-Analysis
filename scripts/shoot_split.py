"""Before and after a bar is clicked, plus the hover card, for review."""
import os
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
OUT = os.environ.get("VT_SHOTS", "_shots")
os.makedirs(OUT, exist_ok=True)

for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1150}).new_page()
    pg.goto(URL, wait_until="networkidle")

    pg.locator(".sbitem", has_text="By occupation group").first.click()
    pg.wait_for_timeout(900)
    pg.locator(".panel").first.screenshot(path=os.path.join(OUT, "split_closed.png"))

    bar = pg.locator(".split svg.chart g.bar").nth(6)
    bar.hover()
    pg.wait_for_timeout(400)
    pg.screenshot(path=os.path.join(OUT, "split_tip.png"))

    bar.click()
    pg.wait_for_timeout(600)
    pg.locator(".panel").first.screenshot(path=os.path.join(OUT, "split_open.png"))

    b.close()
print("shot", OUT)
