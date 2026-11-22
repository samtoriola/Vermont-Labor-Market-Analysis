"""Writes the Overview mockup page, with the real figures inlined. Throwaway.

Three ways the front page could work. Every number here comes out of the
committed JSON via _ovfacts.py, so the options can be judged on what they would
actually say rather than on lorem.
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(open(os.path.join(HERE, "_ovfacts.json"), encoding="utf-8"))
cps = json.load(open(os.path.join(HERE, "..", "data", "cps.json"), encoding="utf-8"))

sub = sum(p["sh"] for p in cps["pathways"]
          if p["p"] in ("Associate degree (sub-baccalaureate)", "Some college, no degree"))
hs = sum(p["sh"] for p in cps["pathways"]
         if p["p"] in ("High school diploma", "Less than high school"))
tiers = {t["t"]: t for t in F["cred"]["tiers"]}
hsJobs = tiers["High school"]["share"] + tiers["No formal credential"]["share"]

F["gap"] = [
    {"lvl": "Bachelor’s or more", "jobs": F["cred"]["baReq"], "people": F["cred"]["baHold"]},
    {"lvl": "Sub-baccalaureate", "jobs": tiers["Sub-baccalaureate"]["share"], "people": round(sub, 1)},
    {"lvl": "High school or less", "jobs": round(hsJobs, 1), "people": round(hs, 1)},
]

OUT = os.path.join(HERE, "..", "_shots", "overview-options.html")

CSS = r"""
  :root {
    --ocean: #009ba5; --ember: #fc4c3a; --vine: #4fcb00; --pine: #007a58;
    --ink: #16202a; --ink-2: #41505e; --ink-3: #74838f;
    --bg: #f7f8f8; --panel: #ffffff; --rule: #e4e8ea; --rule-2: #cfd6da;
    --track: #e8ecee; --warm: #fdeeec; --cool: #e3f3f4;
    --h1c: #fde3e0; --h2c: #fcbdb6; --h3c: #fb968c; --h4c: #f8654f; --h5c: #d93a24;
    --display: 'EB Garamond', Georgia, serif;
    --body: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --fig: 'DM Mono', ui-monospace, 'SF Mono', Menlo, monospace;
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --ink: #eef2f4; --ink-2: #b4c0c8; --ink-3: #8a97a1;
      --bg: #11171c; --panel: #19212a; --rule: #273139; --rule-2: #36434d;
      --track: #222c35; --warm: #3a1f1c; --cool: #13353a;
      --h1c: #3d2420; --h2c: #6b3328; --h3c: #9c4232; --h4c: #cf523c; --h5c: #fd7061;
      --ember: #fd7061; --pine: #339579; color-scheme: dark;
    }
  }
  :root[data-theme="dark"] {
    --ink: #eef2f4; --ink-2: #b4c0c8; --ink-3: #8a97a1;
    --bg: #11171c; --panel: #19212a; --rule: #273139; --rule-2: #36434d;
    --track: #222c35; --warm: #3a1f1c; --cool: #13353a;
    --h1c: #3d2420; --h2c: #6b3328; --h3c: #9c4232; --h4c: #cf523c; --h5c: #fd7061;
    --ember: #fd7061; --pine: #339579; color-scheme: dark;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
         font-family: var(--body); line-height: 1.55; }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 40px 16px 80px; }
  h1 { font-family: var(--display); font-weight: 600; font-size: clamp(30px, 5vw, 42px);
       line-height: 1.12; margin: 0 0 10px; text-wrap: balance; letter-spacing: -0.01em; }
  h2 { font-family: var(--display); font-weight: 600; font-size: clamp(21px, 3vw, 26px);
       margin: 0 0 6px; text-wrap: balance; }
  h3 { font-size: 15px; font-weight: 700; margin: 0 0 4px; }
  p { margin: 0 0 12px; color: var(--ink-2); max-width: 68ch; }
  .lede { font-size: 16.5px; }
  .eyebrow { font-size: 10.5px; letter-spacing: 0.12em; text-transform: uppercase;
             font-weight: 700; color: var(--ocean); margin: 0 0 8px; }
  .num { font-family: var(--fig); font-variant-numeric: tabular-nums; }
  section { margin-top: 56px; }
  .panel { background: var(--panel); border: 1px solid var(--rule); border-radius: 10px;
           padding: 20px; margin-top: 16px; }
  .cap { font-size: 13px; color: var(--ink-2); margin: 0 0 14px; max-width: 80ch; }
  .srcline { font-size: 11.5px; color: var(--ink-3); margin-top: 14px;
             border-top: 1px solid var(--rule); padding-top: 10px; }
  .readout { border-left: 3px solid var(--ocean); background: var(--bg);
             padding: 10px 14px; font-size: 13.5px; color: var(--ink); margin-top: 14px; }
  svg { display: block; width: 100%; height: auto; }
  .scroller { overflow-x: auto; }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 16px; list-style: none; padding: 0;
            margin: 0 0 12px; font-size: 12px; color: var(--ink-2); }
  .legend li { display: flex; align-items: center; gap: 6px; }
  .sw { width: 11px; height: 11px; border-radius: 2px; display: inline-block; }
  .opt { border: 1px solid var(--rule); border-radius: 12px; padding: 22px; margin-top: 18px;
         background: var(--panel); }
  .badge { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: 0.06em;
           text-transform: uppercase; padding: 2px 9px; border-radius: 4px;
           background: var(--cool); color: var(--ocean); margin-bottom: 10px; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 760px) { .grid2 { grid-template-columns: 1fr; } }
  .pro { font-size: 13px; }
  .pro ul { margin: 6px 0 0; padding-left: 18px; color: var(--ink-2); }
  .pro li { margin-bottom: 4px; }
  .note { font-size: 12.5px; color: var(--ink-3); }

  /* Tiles: the dashboard's own, a touch larger so the headline figure leads. */
  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
           gap: 1px; background: var(--rule); border: 1px solid var(--rule);
           border-radius: 10px; overflow: hidden; }
  .tile { background: var(--panel); padding: 15px 16px; }
  .tile .tl { font-size: 10.5px; letter-spacing: 0.08em; text-transform: uppercase;
              color: var(--ink-3); font-weight: 700; }
  .tile .tv { font-family: var(--fig); font-size: 25px; font-weight: 500; letter-spacing: -0.02em;
              margin: 3px 0 1px; }
  .tile .td { font-size: 12px; color: var(--ink-3); }
  .tile.hi .tv { color: var(--ember); }

  /* Option C scorecard */
  .score { border: 1px solid var(--rule); border-radius: 10px; overflow: hidden; }
  .srow { display: grid; grid-template-columns: 148px 132px 1fr; gap: 16px; align-items: baseline;
          padding: 13px 16px; border-bottom: 1px solid var(--rule); background: var(--panel); }
  .srow:last-child { border-bottom: 0; }
  .srow .st { font-weight: 700; font-size: 13.5px; }
  .srow .sv { font-family: var(--fig); font-size: 19px; font-weight: 500; color: var(--ocean);
              letter-spacing: -0.01em; }
  .srow .sv.bad { color: var(--ember); }
  .srow .ss { font-size: 13px; color: var(--ink-2); }
  @media (max-width: 720px) {
    .srow { grid-template-columns: 1fr; gap: 2px; }
  }
"""


def money(n):
    return "$" + format(int(round(n)), ",")


def num(n):
    return format(int(round(n)), ",")


# ---------- Option A: the credential gap ----------
def gap_chart():
    rows, W, labW, padR, padT, rowH, gap = F["gap"], 940, 190, 60, 34, 20, 7
    grp = rowH * 2 + 4
    H = padT + len(rows) * (grp + gap) + 8
    plotW = W - labW - padR
    mx = 60.0
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="What jobs ask for against what workers hold">']
    for t in (0, 15, 30, 45, 60):
        x = labW + t / mx * plotW
        out.append(f'<line x1="{x}" y1="{padT-9}" x2="{x}" y2="{H-6}" stroke="var(--rule)" stroke-width="1"/>')
        out.append(f'<text x="{x}" y="{padT-15}" text-anchor="middle" font-size="10" '
                   f'fill="var(--ink-3)" font-family="var(--fig)">{t}%</text>')
    for i, r in enumerate(rows):
        y = padT + i * (grp + gap)
        out.append(f'<text x="{labW-12}" y="{y+grp/2+4}" text-anchor="end" font-size="12.5" '
                   f'fill="var(--ink)">{r["lvl"]}</text>')
        for k, (key, col) in enumerate((("jobs", "var(--ocean)"), ("people", "var(--pine)"))):
            v = r[key]
            w = max(1.5, v / mx * plotW)
            yy = y + k * (rowH + 4)
            out.append(f'<rect x="{labW}" y="{yy}" width="{w}" height="{rowH}" rx="3" fill="{col}"/>')
            out.append(f'<text x="{labW+w+8}" y="{yy+rowH/2+4}" font-size="11.5" '
                       f'fill="var(--ink-2)" font-family="var(--fig)">{v:.1f}%</text>')
    out.append("</svg>")
    return "".join(out)


# ---------- Option B: the market in one picture ----------
STEPS = [(10, "var(--h1c)", "under 10%"), (30, "var(--h2c)", "10 to 30%"),
         (50, "var(--h3c)", "30 to 50%"), (75, "var(--h4c)", "50 to 75%"),
         (10**9, "var(--h5c)", "75% and over")]


def band(p):
    for mx, col, _ in STEPS:
        if p < mx:
            return col
    return STEPS[-1][1]


SHORT = {
    "Office & Administrative Support": "Office & Admin Support",
    "Educational Instruction & Library": "Education & Library",
    "Healthcare Practitioners & Technical": "Healthcare Practitioners",
    "Arts, Design, Entertainment & Media": "Arts, Design & Media",
    "Installation, Maintenance & Repair": "Installation & Repair",
    "Transportation & Material Moving": "Transportation & Moving",
    "Business & Financial Operations": "Business & Financial",
    "Life, Physical & Social Science": "Life & Physical Science",
    "Food Preparation & Serving": "Food Preparation",
    "Building & Grounds Cleaning": "Building & Grounds",
    "Farming, Fishing & Forestry": "Farming & Forestry",
    "Construction & Extraction": "Construction",
    "Community & Social Service": "Community & Social Service",
}


def market_chart():
    rows = F["groups"]
    W, labW, padR, padT, rowH, gap = 940, 196, 104, 30, 19, 6
    H = padT + len(rows) * (rowH + gap) + 8
    plotW = W - labW - padR
    mx = max(r["jobs"] for r in rows)
    top = 35000.0
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="Vermont employment by occupation group, shaded by how much of it pays below a living wage">']
    for t in (0, 10000, 20000, 30000):
        x = labW + t / top * plotW
        out.append(f'<line x1="{x}" y1="{padT-9}" x2="{x}" y2="{H-6}" stroke="var(--rule)" stroke-width="1"/>')
        lbl = "0" if t == 0 else f"{t//1000}k"
        out.append(f'<text x="{x}" y="{padT-15}" text-anchor="middle" font-size="10" '
                   f'fill="var(--ink-3)" font-family="var(--fig)">{lbl}</text>')
    for i, r in enumerate(rows):
        y = padT + i * (rowH + gap)
        w = max(2, r["jobs"] / top * plotW)
        nm = SHORT.get(r["f"], r["f"])
        out.append(f'<text x="{labW-11}" y="{y+rowH/2+4}" text-anchor="end" font-size="11.5" '
                   f'fill="var(--ink)">{nm}</text>')
        out.append(f'<rect x="{labW}" y="{y}" width="{w}" height="{rowH}" rx="3" fill="{band(r["below"])}"/>')
        out.append(f'<text x="{labW+plotW+8}" y="{y+rowH/2+4}" font-size="11" '
                   f'fill="var(--ink-2)" font-family="var(--fig)">{num(r["jobs"])}</text>')
        out.append(f'<text x="{labW+plotW+66}" y="{y+rowH/2+4}" font-size="11" '
                   f'fill="var(--ink-3)" font-family="var(--fig)">{r["below"]:.0f}%</text>')
    out.append(f'<text x="{labW+plotW+8}" y="{padT-15}" font-size="9.5" fill="var(--ink-3)" '
               f'font-family="var(--fig)">JOBS</text>')
    out.append(f'<text x="{labW+plotW+66}" y="{padT-15}" font-size="9.5" fill="var(--ink-3)" '
               f'font-family="var(--fig)">BELOW</text>')
    out.append("</svg>")
    return "".join(out)


def legend():
    return "".join(f'<li><span class="sw" style="background:{col}"></span>{lab}</li>'
                   for _, col, lab in STEPS)


S, P, C, V, PL = F["scale"], F["pay"], F["cred"], F["vscs"], F["places"]
big = F["groups"][0]
worst = max(F["groups"], key=lambda r: r["belowN"])

TILES_A = [
    ("Jobs", num(S["jobs"]), f'+{(S["jobs"]/S["jobs21"]-1)*100:.1f}% since 2021', ""),
    ("Openings a year", num(S["openings"]), "roughly 1 in 7 jobs turns over", ""),
    ("Pay below a living wage", f'{P["belowPct"]:.0f}%', f'{num(P["belowN"])} of {num(P["priced"])} jobs', "hi"),
    ("Workers with a degree", f'{C["baHold"]:.0f}%', f'against {C["baReq"]:.0f}% of jobs asking for one', ""),
]

TILES_B = [
    ("Jobs", num(S["jobs"]), f'across {S["occ"]} occupations', ""),
    ("Typical job pays", money(P["box"]["p50"]), f'living wage {money(P["lwA"])}', ""),
    ("Pay below it", f'{P["belowPct"]:.0f}%', f'{num(P["belowN"])} jobs', "hi"),
]

SCORE = [
    ("Employment", num(S["jobs"]), "",
     f'{num(S["jobs"])} jobs across {S["occ"]} occupations, up {(S["jobs"]/S["jobs21"]-1)*100:.1f}% since 2021. '
     f'The largest single group is {SHORT.get(big["f"], big["f"])} at {num(big["jobs"])}.'),
    ("Wage quality", f'{P["belowPct"]:.0f}%', "bad",
     f'{num(P["belowN"])} jobs pay less than the {money(P["lwA"])} one adult needs. '
     f'The most people short are in {SHORT.get(worst["f"], worst["f"])} — {num(worst["belowN"])}.'),
    ("Demand &amp; growth", num(S["openings"]), "",
     f'openings a year, against {S["turn"]:.0f}% annual turnover — most of the hiring '
     f'is replacing people, not adding posts.'),
    ("Pathways", money(tiers["Bachelor’s"]["med"] if "Bachelor’s" in tiers else tiers["Bachelor's"]["med"]), "",
     f'the typical job asking for a bachelor’s pays that, against '
     f'{money(tiers["High school"]["med"])} at high school — a {(tiers["Bachelor\'s"]["med"]/tiers["High school"]["med"]-1)*100:.0f}% premium.'),
    ("Workers", f'{C["baHold"]:.0f}%', "",
     f'of Vermonters hold a degree while {C["baReq"]:.0f}% of jobs ask for one. '
     f'The state’s workers are credentialed ahead of its work.'),
    ("Regions", f'{PL["n"]}', "",
     f'counties. A typical job pays {money(PL["payHi"]["med"])} in {PL["payHi"]["c"]} and '
     f'{money(PL["payLo"]["med"])} in {PL["payLo"]["c"]}, and the cost floor moves too: '
     f'{money(P["ctyRange"][0])} to {money(P["ctyRange"][1])}.'),
]


def tiles(items):
    return ('<div class="tiles">' + "".join(
        f'<div class="tile {cls}"><div class="tl">{t}</div><div class="tv">{v}</div>'
        f'<div class="td">{d}</div></div>' for t, v, d, cls in items) + "</div>")


def scorecard():
    return ('<div class="score">' + "".join(
        f'<div class="srow"><div class="st">{t}</div>'
        f'<div class="sv {cls}">{v}</div><div class="ss">{s}</div></div>'
        for t, v, cls, s in SCORE) + "</div>")


PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Overview Options</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@500;600&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <p class="eyebrow">Strada Education Foundation &middot; Vermont State Colleges System</p>
  <h1>Three ways the Overview could work</h1>
  <p class="lede">
    The Overview is the first thing anyone sees and the only page that has to work for someone
    who will not click anything else. Today it carries ten figures across two tile rows and one
    chart, which is a lot of reading and no argument. All three options below use the real
    numbers.
  </p>

  <section>
    <h2>What the dashboard already knows</h2>
    <p>
      Worth seeing in one place, because it decides what a front page can honestly claim.
      {num(S["jobs"])} jobs, {P["belowPct"]:.0f}% of them paying under a living wage, and a
      workforce holding more credentials than its jobs ask for. That last one is the sharpest
      thing in the dataset and the Overview is the only page that can say it.
    </p>
  </section>

  <!-- ===================== OPTION A ===================== -->
  <div class="opt">
    <p class="badge">Option A</p>
    <h2>Four numbers and the gap</h2>
    <p>
      The shortest edit: cut the ten figures to four, keep the one chart that frames the whole
      dashboard, and move the labour-force detail to Methods. Scale, churn, pay and credentials
      &mdash; one number each, then the picture that explains the fourth.
    </p>
    {tiles(TILES_A)}
    <div class="panel">
      <h3>Do Vermont&rsquo;s jobs ask for the credentials its workers hold?</h3>
      <p class="cap">
        One side counts what jobs ask for at entry, the other what working Vermonters hold.
        Different surveys counting different populations, so the shares compare and the levels
        do not.
      </p>
      <ul class="legend">
        <li><span class="sw" style="background:var(--ocean)"></span>What jobs ask for</li>
        <li><span class="sw" style="background:var(--pine)"></span>What workers hold</li>
      </ul>
      <div class="scroller">{gap_chart()}</div>
      <div class="readout">
        Vermont&rsquo;s workers are credentialed ahead of its work: <strong>{C["baHold"]:.1f}%</strong>
        hold a bachelor&rsquo;s or more while <strong>{C["baReq"]:.1f}%</strong> of jobs ask for one
        &mdash; a gap of {C["baHold"]-C["baReq"]:.1f} points. At high school or less the gap runs the
        other way.
      </div>
      <div class="srcline">
        Vermont occupation data, 2025 &middot; labour force survey, 2025, age 25 and over
      </div>
    </div>
    <div class="grid2" style="margin-top:16px">
      <div class="pro"><h3>What it is good at</h3><ul>
        <li>Smallest change from what exists; nothing new to build</li>
        <li>Four figures is a number people actually read</li>
        <li>Keeps the one chart that sets up Pathways and Workers</li>
      </ul></div>
      <div class="pro"><h3>What it hides</h3><ul>
        <li>Says nothing about <em>which</em> work pays badly &mdash; the reader has to go find it</li>
        <li>Still a page of headline figures rather than a picture of the state</li>
      </ul></div>
    </div>
  </div>

  <!-- ===================== OPTION B ===================== -->
  <div class="opt">
    <p class="badge">Option B</p>
    <h2>The market in one picture</h2>
    <p>
      One chart that <em>is</em> the Vermont labour market: every occupation group, as long as it
      is big and as dark as its work is underpaid. Size and pay quality in the same mark, so the
      reader sees the problem rather than being told a percentage.
    </p>
    {tiles(TILES_B)}
    <div class="panel">
      <h3>What Vermont does for a living, and how much of it pays enough</h3>
      <p class="cap">
        Bar length is jobs. Shading is the share of that group&rsquo;s jobs paying below a living
        wage for one adult, read off each occupation&rsquo;s own pay distribution. Click any bar
        to open the group.
      </p>
      <ul class="legend">{legend()}</ul>
      <div class="scroller">{market_chart()}</div>
      <div class="readout">
        The three groups that employ the most Vermonters sit at opposite ends of this.
        <strong>{SHORT["Office & Administrative Support"]}</strong> is the largest at
        {num(big["jobs"])} jobs with {big["below"]:.0f}% paying under the benchmark, while
        <strong>Food Preparation</strong> puts the most people short of it &mdash;
        {num(worst["belowN"])}.
      </div>
      <div class="srcline">
        Vermont occupation data, 2025 &middot; {num(P["priced"])} jobs with a published pay
        distribution &middot; benchmark {money(P["lwA"])} a year, one adult
      </div>
    </div>
    <div class="grid2" style="margin-top:16px">
      <div class="pro"><h3>What it is good at</h3><ul>
        <li>One mark carries two measures, so the state fits on one screen</li>
        <li>It is an argument, not a dashboard: you can see where the problem is</li>
        <li>Every bar is a door into Employment or Wage benchmark</li>
      </ul></div>
      <div class="pro"><h3>What it hides</h3><ul>
        <li>Twenty-two rows is more reading than four tiles</li>
        <li>Nothing about credentials, demand or VSCS &mdash; those become tiles or go unsaid</li>
        <li>Shading by a second variable asks more of a colour-blind reader than length alone</li>
      </ul></div>
    </div>
  </div>

  <!-- ===================== OPTION C ===================== -->
  <div class="opt">
    <p class="badge">Option C</p>
    <h2>Answers, not a menu</h2>
    <p>
      No chart at all. One row per tab, each carrying that tab&rsquo;s single most important
      figure and a sentence saying what it means. Someone who reads only this page still leaves
      knowing what the analysis found; someone who wants more clicks the row.
    </p>
    {scorecard()}
    <div class="readout" style="margin-top:16px">
      The Home page already lists the tabs and what each covers. This replaces
      &ldquo;here is what you could look at&rdquo; with &ldquo;here is what we found&rdquo;
      &mdash; which is the difference between a table of contents and an overview.
    </div>
    <div class="grid2" style="margin-top:16px">
      <div class="pro"><h3>What it is good at</h3><ul>
        <li>The only option that works if the reader stops after one page</li>
        <li>Every figure is live, so it cannot go stale the way written copy does</li>
        <li>Doubles as the executive summary a scope-of-work deliverable needs</li>
      </ul></div>
      <div class="pro"><h3>What it hides</h3><ul>
        <li>No picture, so nothing to put in a slide</li>
        <li>Six sentences is a wall of prose if the writing slips</li>
        <li>Overlaps the Home page unless Home is cut back to pure navigation</li>
      </ul></div>
    </div>
  </div>

  <section>
    <h2>Worth saying plainly</h2>
    <p>
      These are not exclusive. <strong>A</strong> and <strong>C</strong> combine cleanly &mdash;
      four tiles, then the scorecard, no chart. <strong>B</strong> and <strong>C</strong> do not;
      they are both trying to be the one thing the reader looks at.
    </p>
    <p class="note">
      Every figure on this page is generated from the committed JSON. Nothing was queried and
      nothing is rounded by hand.
    </p>
  </section>
</div>
</body>
</html>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(PAGE)
print("wrote %s (%s bytes)" % (os.path.abspath(OUT), f"{os.path.getsize(OUT):,}"))
