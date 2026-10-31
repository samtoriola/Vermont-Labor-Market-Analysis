"""The merged panels, one shot per section, for review."""
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

SHOTS = [
    ("Industry sectors", "Age mix", "m_sec_age"),
    ("By occupation group", "Age mix", "m_fam_age"),
    ("By credential level", "Range of outcomes", "m_cred"),
]

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1680, "height": 1150}).new_page()
    pg.goto(URL, wait_until="networkidle")
    for section, measure, name in SHOTS:
        pg.locator(".sbitem", has_text=section).first.click()
        pg.wait_for_timeout(800)
        pg.locator(".rankctl .chips button", has_text=measure).first.click()
        pg.wait_for_timeout(700)
        pg.locator(".view").first.screenshot(path=os.path.join(OUT, name + ".png"))
        print("shot", name)
    b.close()
