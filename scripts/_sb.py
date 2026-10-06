import sys, time, urllib.request, pathlib
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
URL = "http://127.0.0.1:3162/"
OUT = pathlib.Path(__file__).resolve().parent.parent / "_shots"
for _ in range(60):
    try:
        urllib.request.urlopen(URL, timeout=3).read(); break
    except Exception: time.sleep(1)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width":1440,"height":1000}).new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("localStorage.clear()"); pg.reload(wait_until="networkidle")

    gap = pg.evaluate("""() => {
      const sb = document.querySelector('.sidebar').getBoundingClientRect();
      const w = document.querySelector('.wrap').getBoundingClientRect();
      const p = document.querySelector('.homecard, .panel');
      return {sidebarRight: Math.round(sb.right),
              contentLeft: Math.round(p ? p.getBoundingClientRect().left : w.left),
              gap: Math.round((p ? p.getBoundingClientRect().left : w.left) - sb.right)};
    }""")
    print("spacing:", gap)
    print("sidebar item font:",
          pg.evaluate("getComputedStyle(document.querySelector('.sbitem')).fontSize"))
    print("group head font:",
          pg.evaluate("getComputedStyle(document.querySelector('.sbhead')).fontSize"))

    print("\n-- collapsing a topic --")
    before = pg.locator(".sbitem").count()
    pg.locator(".sbhead", has_text="Wage quality").first.click(); pg.wait_for_timeout(350)
    after = pg.locator(".sbitem").count()
    print(f"  items {before} -> {after}  (hid {before-after})")
    pg.reload(wait_until="networkidle"); pg.wait_for_timeout(500)
    print(f"  still collapsed after reload: {pg.locator('.sbitem').count() == after}")

    print("\n-- the open topic cannot be hidden --")
    pg.locator(".sbitem", has_text="Median pay by size").first.click(); pg.wait_for_timeout(450)
    pg.locator(".sbhead", has_text="Wage quality").first.click(); pg.wait_for_timeout(350)
    vis = pg.locator(".sbitem", has_text="Median pay by size").count()
    print(f"  current section still listed: {vis > 0}")

    pg.locator(".sbitem", has_text="Home").first.click(); pg.wait_for_timeout(450)
    pg.screenshot(path=str(OUT/"sidebar.png"))
    print("\nsidebar.png | errors:", len(errs))
    b.close()
