"""Verify the PNG export: the button appears only where there is a chart, the
download fires, and the image that comes back is the right size and not blank."""
import os, pathlib, struct
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:%s/" % os.environ.get("VT_PORT", "3163")
OUT = pathlib.Path(__file__).resolve().parent.parent / "_shots"
OUT.mkdir(exist_ok=True)


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    return struct.unpack(">II", head[16:24])


errs, perrs = [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1700, "height": 1000}, accept_downloads=True)
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: perrs.append(str(e)))
    pg.goto(URL)
    pg.wait_for_timeout(1800)

    print("--- the button follows the charts ---")
    checks = [
        ("Median pay by size", True),
        ("Worker earnings", True),
        ("What the job requires", True),
        ("All 14 counties", False),   # a table
        ("How the index is built", False),  # prose
    ]
    for label, want in checks:
        pg.locator(".sbitem", has_text=label).first.click()
        pg.wait_for_timeout(900)
        charts = pg.locator(".panel svg.chart").count()
        buttons = pg.locator(".panel-actions .iconbtn").count()
        ok = (buttons > 0) == want
        print("  %-26s charts=%-2d png buttons=%-2d %s"
              % (label[:26], charts, buttons, "ok" if ok else "MISMATCH"))
        assert ok, "PNG button presence is wrong on " + label

    print("\n--- the download produces a real image ---")
    for label in ["Median pay by size", "What the job requires", "Jobs by family"]:
        pg.locator(".sbitem", has_text=label).first.click()
        pg.wait_for_timeout(1000)
        with pg.expect_download(timeout=30000) as dl:
            pg.locator(".panel-actions .iconbtn").first.click()
        d = dl.value
        dest = OUT / d.suggested_filename
        d.save_as(str(dest))
        w, h = png_size(dest)
        size_kb = dest.stat().st_size / 1024
        print("  %-26s %-44s %dx%d  %.0f KB"
              % (label[:26], d.suggested_filename, w, h, size_kb))
        assert w > 800 and h > 300, "image too small to be the chart"
        assert size_kb > 8, "image suspiciously small -- probably blank"

    print("\nconsole errors: %d | page errors: %d" % (len(errs), len(perrs)))
    for e in perrs[:4]:
        print("  PAGE:", e[:160])
    for e in errs[:4]:
        print("  CON:", e[:160])
    b.close()

print("\nRESULT:", "CLEAN" if not perrs else "ERRORS")
