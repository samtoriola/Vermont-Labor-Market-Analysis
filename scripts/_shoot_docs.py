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
    pg = b.new_context(viewport={"width": 1680, "height": 1200}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()"); pg.reload(wait_until="networkidle")
    for name in ("Methods", "About"):
        pg.locator(".sbitem, .navbtn", has_text=name).first.click()
        pg.wait_for_timeout(1100)
        pg.screenshot(path="%s/doc_%s.png" % (OUT, name.lower()), full_page=True)
        n = pg.locator(".view .panel, .view .pnl").count()
        print("%-8s panels=%d tables=%d" % (name, n, pg.locator(".view table").count()))
    print("page errors:", errs[:3] if errs else 0)
    b.close()
