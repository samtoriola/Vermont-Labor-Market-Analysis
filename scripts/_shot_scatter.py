"""Eyes on the Every-occupation scatter: count the points by colour, then shoot it."""
import io
import json
import os
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = r"C:\Users\sam.toriola\AppData\Local\Temp\_q2shots"
os.makedirs(SHOTS, exist_ok=True)

LC = json.load(io.open(os.path.join(HERE, "..", "data", "lightcast.json"), encoding="utf-8"))
LWA = 23.95 * 2080

priced = [o for o in LC["allOcc"] if o.get("m") and o.get("hasLadder", True)]
URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3205")
for _ in range(40):
    try:
        urllib.request.urlopen(URL, timeout=3).read()
        break
    except Exception:
        time.sleep(1)

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1300}).new_page()
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()")
    pg.reload(wait_until="networkidle")
    pg.locator(".sbitem", has_text="Wage benchmark").first.click()
    pg.wait_for_timeout(600)
    pg.locator(".rankctl button", has_text="Every occupation").first.click()
    pg.wait_for_timeout(900)

    fills = pg.eval_on_selector_all(
        "svg.chart circle",
        "els => els.map(e => e.getAttribute('fill'))",
    )
    from collections import Counter
    print("point fills:", Counter(fills))

    # What the data says the split should be.
    below = sum(1 for o in priced if o["m"] < LWA)
    print("data: %d below, %d at or above, %d plotted" % (below, len(priced) - below, len(priced)))

    print("legend:", " | ".join(pg.locator(".legend li").all_inner_texts()))
    cap = pg.locator(".panel", has_text="Does a bigger occupation").first
    print("cap:", " ".join(cap.locator(".cap").first.inner_text().split())[:300])

    cap.screenshot(path=os.path.join(SHOTS, "scatter.png"))
    b.close()
print("shot:", os.path.join(SHOTS, "scatter.png"))
