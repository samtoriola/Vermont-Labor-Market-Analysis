"""Crop each new chart out of the full-page shots so they can be eyeballed."""
import pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(__file__).resolve().parent.parent / "_shots"
URL = "http://127.0.0.1:3130/"
WANT = [
    ("structure", "Where pay actually sits", "01-families-dotrows"),
    ("wage", "Where pay sits, by occupation size", "02-size-dotcolumns"),
    ("wage", "What people actually earn", "03-people-dotcolumns"),
    ("wage", "mean against median", "04-percentile-ladder"),
    ("pathways", "by what the job requires", "05-credential-dotcolumns"),
    ("pathways", "by what people hold", "06-credential-people"),
]
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_context(viewport={"width": 1400, "height": 1000}).new_page()
    pg.goto(URL, wait_until="networkidle")
    for tab, needle, name in WANT:
        pg.click(f"#tab-{tab}")
        pg.wait_for_timeout(700)
        p = pg.locator(f"#view-{tab} .panel").filter(has_text=needle).first
        if not p.count():
            print(f"  {name}: no panel on {tab} matching {needle!r}")
            continue
        title = p.locator("h3, h2").first.inner_text()
        p.scroll_into_view_if_needed()
        pg.wait_for_timeout(250)
        p.screenshot(path=str(OUT / f"{name}.png"))
        print(f"  {name}.png  <- {tab}: {title!r}")
    b.close()
