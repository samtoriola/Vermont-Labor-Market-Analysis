"""Writes the Opportunities prototype page. Throwaway.

Four options across the tab's two sections, drawn in the dashboard's own visual
language. Every figure comes out of _oppfacts.py, which recomputes them from the
committed JSON -- no query is run.
"""
import io
import json
import math
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(io.open(os.path.join(HERE, "_oppfacts.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "..", "_shots", "opportunities-options.html")

TOP = F["top"]
CAND = F["cand"]
LWA = F["lwa"]
LW = F["lw"]
MIN = F["minOpen"]
COMPS = [("s_size", "Employment"), ("s_growth", "Growth"),
         ("s_postings", "Advertising"), ("s_pay", "Pay")]
PIPE = ["No VSCS pipeline", "Thin pipeline", "Established pipeline"]


def money(v):
    return "$" + format(int(round(v)), ",")


def fmt(v):
    return format(int(round(v)), ",")


def short(n, w=30):
    if len(n) <= w:
        return n
    cut = n[:w].rsplit(" ", 1)[0]
    return (cut or n[:w]) + "…"


def spread(r):
    c = [r[k] for k, _ in COMPS]
    return max(c) - min(c)


# ---------------------------------------------------------------- chart A ---
# The score, unpacked. Bar length is still the score; the segments are where it
# came from, each component contributing up to a quarter of it.
def chart_a(n=14):
    rows = TOP[:n]
    W, padL, plotW, padT, rowH = 1180, 262, 700, 54, 31
    H = padT + len(rows) * rowH + 16
    X = lambda v: v / 100 * plotW
    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Opportunity score, '
         'split into the four ranks it is the mean of">' % (W, H)]
    for t in (25, 50, 75, 100):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (padL + X(t), padT - 12, padL + X(t), padT + len(rows) * rowH - 8))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%d</text>'
                 % (padL + X(t), padT - 20, t))
    s.append('<text class="colhead" x="1176" y="%d" text-anchor="end">SCORE</text>' % (padT - 20))
    for i, r in enumerate(rows):
        y = padT + i * rowH
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 14, y + 16, short(r["n"], 38)))
        x = padL
        for ci, (k, _) in enumerate(COMPS):
            w = X(r[k] / 4)
            s.append('<rect class="c%d" x="%.1f" y="%d" width="%.1f" height="21"/>'
                     % (ci + 1, x, y + 1, w))
            x += w
        s.append('<text class="fig" x="1176" y="%d" text-anchor="end">%.1f</text>'
                 % (y + 16, r["sc"]))
        if spread(r) >= 50:
            s.append('<text class="flag" x="%.1f" y="%d">%d&#8211;%d</text>'
                     % (x + 9, y + 16, min(r[k] for k, _ in COMPS),
                        max(r[k] for k, _ in COMPS)))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart B ---
# The same four ranks as a grid, which reads down a column as well as across a row.
def chart_b(n=14):
    rows = TOP[:n]
    W, padL, padT, cw, rowH = 1180, 300, 64, 118, 30
    H = padT + len(rows) * rowH + 16

    def band(v):
        return "--ord%d" % (1 + min(4, int(v / 20.01)))

    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Each occupation\'s four '
         'percentile ranks as a grid">' % (W, H)]
    for ci, (_, lab) in enumerate(COMPS):
        s.append('<text class="colhead" x="%d" y="%d" text-anchor="middle">%s</text>'
                 % (padL + ci * cw + cw / 2, padT - 14, lab.upper()))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">SCORE</text>'
             % (padL + 4 * cw + 92, padT - 14))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">WIDEST GAP</text>'
             % (padL + 4 * cw + 232, padT - 14))
    for i, r in enumerate(rows):
        y = padT + i * rowH
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 16, y + 19, short(r["n"], 42)))
        for ci, (k, _) in enumerate(COMPS):
            v = r[k]
            s.append('<rect x="%d" y="%d" width="%d" height="25" rx="3" fill="var(%s)"/>'
                     % (padL + ci * cw + 1, y + 1, cw - 3, band(v)))
            s.append('<text class="cell%s" x="%d" y="%d" text-anchor="middle">%d</text>'
                     % (" hi" if v >= 60 else "", padL + ci * cw + cw / 2, y + 19, v))
        s.append('<text class="fig" x="%d" y="%d" text-anchor="end">%.1f</text>'
                 % (padL + 4 * cw + 92, y + 19, r["sc"]))
        s.append('<text class="%s" x="%d" y="%d" text-anchor="end">%d points</text>'
                 % ("flag" if spread(r) >= 50 else "figsub",
                    padL + 4 * cw + 232, y + 19, spread(r)))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart C ---
# Openings against the pipeline, with the pipeline as three lanes rather than as
# a number. Sixteen of these occupations have exactly zero graduates attributed,
# which no continuous axis draws honestly.
def chart_c():
    W, padL, padR, padT, laneH = 1180, 196, 44, 48, 116
    pw = W - padL - padR
    H = padT + 3 * laneH + 54
    XMIN, XMAX = 40.0, 400.0
    X = lambda v: padL + (min(v, XMAX) - XMIN) / (XMAX - XMIN) * pw

    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Screened occupations '
         'by annual openings, in three lanes by how much VSCS already produces">' % (W, H)]
    for t in (100, 200, 300, 400):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (X(t), padT, X(t), padT + 3 * laneH))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%d</text>'
                 % (X(t), padT + 3 * laneH + 20, t))

    for li, pipe in enumerate(PIPE):
        mine = sorted([r for r in CAND if r["pipeline"] == pipe], key=lambda r: -r["o"])
        y0 = padT + li * laneH
        mid = y0 + laneH / 2
        if li == 0:
            s.append('<rect class="quad" x="%d" y="%d" width="%.1f" height="%d"/>'
                     % (padL, y0 + 3, pw, laneH - 6))
        s.append('<line class="lane" x1="%d" y1="%d" x2="%d" y2="%d"/>'
                 % (padL, y0, padL + pw, y0))
        s.append('<text class="clab" x="%d" y="%.1f" text-anchor="end">%s</text>'
                 % (padL - 18, mid - 4, pipe))
        # Two lines: one line of this ran off the left edge of the canvas.
        s.append('<text class="figsub" x="%d" y="%.1f" text-anchor="end">%d occupations</text>'
                 % (padL - 18, mid + 13, len(mine)))
        s.append('<text class="figsub" x="%d" y="%.1f" text-anchor="end">%s openings a year</text>'
                 % (padL - 18, mid + 28, fmt(sum(r["o"] for r in mine))))
        # Spread within the lane so equal-openings points do not land on each other.
        for i, r in enumerate(mine):
            dy = ((i % 5) - 2) * 15.0
            s.append('<circle class="%s" cx="%.1f" cy="%.1f" r="%.1f"/>'
                     % ("pt gap" if li == 0 else "pt", X(r["o"]), mid + dy,
                        3.4 + min(4.2, (r["j"] or 0) ** 0.4 / 7)))
        if li == 0:
            # Name the four that are hiring hardest with nothing behind them.
            for i, r in enumerate(mine[:4]):
                yy = mid + ((i % 5) - 2) * 15.0
                s.append('<text class="plab on" x="%.1f" y="%.1f">%s</text>'
                         % (X(r["o"]) + 9, yy + 4, short(r["n"], 32)))
    s.append('<line class="lane" x1="%d" y1="%d" x2="%d" y2="%d"/>'
             % (padL, padT + 3 * laneH, padL + pw, padT + 3 * laneH))
    s.append('<text class="axlab" x="%.1f" y="%d" text-anchor="middle">Openings a year</text>'
             % (padL + pw / 2, H - 12))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart D ---
# The same screen as a ranking, which is what the table is -- but with the
# pipeline carried by the bar rather than printed in a column.
def chart_d(n=16):
    rows = sorted(CAND, key=lambda r: -r["o"])[:n]
    W, padL, plotW, padT, rowH = 1180, 290, 600, 54, 30
    H = padT + len(rows) * rowH + 16
    mx = max(r["o"] for r in rows)
    X = lambda v: v / mx * plotW
    col = {"No VSCS pipeline": "--ord5", "Thin pipeline": "--ord3",
           "Established pipeline": "--ord1"}
    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Screened occupations '
         'by annual openings, shaded by how much VSCS already produces">' % (W, H)]
    for t in (100, 200, 300):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (padL + X(t), padT - 12, padL + X(t), padT + len(rows) * rowH - 8))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%d</text>'
                 % (padL + X(t), padT - 20, t))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">OPENINGS</text>'
             % (W - 196, padT - 20))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">GRADUATES</text>'
             % (W - 96, padT - 20))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">SIGNALS</text>'
             % (W - 4, padT - 20))
    for i, r in enumerate(rows):
        y = padT + i * rowH
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 14, y + 16, short(r["n"], 40)))
        s.append('<rect x="%d" y="%d" width="%.1f" height="21" rx="3" fill="var(%s)"/>'
                 % (padL, y + 1, X(r["o"]), col[r["pipeline"]]))
        s.append('<text class="fig" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (W - 196, y + 16, fmt(r["o"])))
        s.append('<text class="%s" x="%d" y="%d" text-anchor="end">%s</text>'
                 % ("flag" if r["linked"] == 0 else "fig", W - 96, y + 16,
                    "none" if r["linked"] == 0 else ("%.1f" % r["linked"])))
        s.append('<text class="figsub" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (W - 4, y + 16, "●" * r["nSig"] + "○" * (3 - r["nSig"])))
    s.append("</svg>")
    return "\n".join(s)


# -------------------------------------------------------------------- page ---
def srcblock(line, uses):
    rows = "".join("<tr><th>%s</th><td>%s</td></tr>" % (a, b) for a, b in uses)
    return ('<p class="src">%s</p>'
            '<details class="uses"><summary>What this chart uses</summary>'
            '<table>%s</table></details>' % (line, rows))


nNone = len([r for r in CAND if r["pipeline"] == "No VSCS pipeline"])
nThin = len([r for r in CAND if r["pipeline"] == "Thin pipeline"])
nEst = len(CAND) - nNone - nThin
noneTop = sorted([r for r in CAND if r["pipeline"] == "No VSCS pipeline"],
                 key=lambda r: -r["o"])
noneOpen = sum(r["o"] for r in noneTop)
wide = sorted(TOP[:30], key=lambda r: -spread(r))[0]
rn = [r for r in TOP if r["n"] == "Registered Nurses"][0]
cna = [r for r in TOP if r["n"] == "Computer Network Architects"][0]

CSS = r"""
:root{
  --s1:#009ba5; --ord1:#ccebed; --ord2:#99d7db; --ord3:#66c3c9; --ord4:#33afb7; --ord5:#009ba5;
  --c1:#009ba5; --c2:#4fb3bb; --c3:#99d7db; --c4:#cfe9eb;
  --ink:#16202a; --ink-2:#41505e; --ink-3:#74838f; --flag:#b4532f;
  --bg:#f7f8f8; --panel:#fff; --rule:#e4e8ea; --rule-2:#cfd6da; --track:#e8ecee; --cool:#e9f5f6;
  --quad:#ddf1f2;
  --display:'EB Garamond',Georgia,serif;
  --body:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --fig:'DM Mono',ui-monospace,'SF Mono',Menlo,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#eef2f4; --ink-2:#b4c0c8; --ink-3:#8a97a1; --flag:#e8a088;
  --bg:#11171c; --panel:#19212a; --rule:#273139; --rule-2:#36434d; --track:#222c35; --cool:#14313a;
  --quad:#16343a;
  --s1:#33afb7; --ord1:#0f3a3f; --ord2:#15606a; --ord3:#008c9b; --ord4:#33afb7; --ord5:#66c3c9;
  --c1:#66c3c9; --c2:#33afb7; --c3:#15606a; --c4:#0f3a3f;
  color-scheme:dark;
}}
:root[data-theme="dark"]{
  --ink:#eef2f4; --ink-2:#b4c0c8; --ink-3:#8a97a1; --flag:#e8a088;
  --bg:#11171c; --panel:#19212a; --rule:#273139; --rule-2:#36434d; --track:#222c35; --cool:#14313a;
  --quad:#16343a;
  --s1:#33afb7; --ord1:#0f3a3f; --ord2:#15606a; --ord3:#008c9b; --ord4:#33afb7; --ord5:#66c3c9;
  --c1:#66c3c9; --c2:#33afb7; --c3:#15606a; --c4:#0f3a3f;
  color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1280px;margin:0 auto;
  padding-left:max(16px,env(safe-area-inset-left,0px));
  padding-right:max(16px,env(safe-area-inset-right,0px));
  padding-block:30px 72px}
h1{font-family:var(--display);font-size:33px;line-height:1.15;margin:0 0 6px;
  font-weight:600;text-wrap:balance}
.sub{color:var(--ink-2);margin:0 0 6px;max-width:68ch}
.meta{color:var(--ink-3);font-size:13px;margin:0 0 30px}
h2{font-family:var(--display);font-size:25px;margin:0 0 4px;font-weight:600;text-wrap:balance}
.part{font-family:var(--display);font-size:20px;margin:0 0 4px;font-weight:600;
  color:var(--ink-2);border-top:2px solid var(--rule-2);padding-top:14px}
.opt{margin:0 0 14px}
.opt .tag{display:inline-block;font-size:11px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--s1);font-weight:600;margin-bottom:3px}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:9px;
  padding:20px 22px 16px;margin:0 0 30px}
.panel h3{font-family:var(--display);font-size:21px;margin:0 0 5px;font-weight:600;text-wrap:balance}
.cap{color:var(--ink-2);font-size:13.5px;margin:0 0 16px;max-width:94ch}
.chart{width:100%;height:auto;display:block;overflow:visible}
.cwrap{overflow-x:auto}
.note{background:var(--cool);border-left:3px solid var(--s1);border-radius:0 5px 5px 0;
  padding:11px 15px;margin:16px 0 0;font-size:14px;color:var(--ink)}
.src{color:var(--ink-3);font-size:11.5px;margin:16px 0 0;padding-top:11px;
  border-top:1px solid var(--rule);line-height:1.5}
.uses{margin:9px 0 0;font-size:12px}
.uses summary{color:var(--s1);cursor:pointer;font-weight:500}
.uses table{border-collapse:collapse;margin:9px 0 2px;width:100%}
.uses th{text-align:left;color:var(--ink-3);font-weight:500;white-space:nowrap;
  padding:3px 16px 3px 0;vertical-align:top;width:1%}
.uses td{padding:3px 0;color:var(--ink-2);font-family:var(--fig);font-size:11.5px}
.grid{stroke:var(--rule);stroke-width:1}
.tick{font-family:var(--fig);font-size:10px;fill:var(--ink-3)}
.colhead{font-family:var(--body);font-size:10px;letter-spacing:.09em;fill:var(--ink-3);font-weight:500}
.clab{font-family:var(--body);font-size:12px;fill:var(--ink)}
.fig{font-family:var(--fig);font-size:11.5px;fill:var(--ink);font-weight:500}
.figsub{font-family:var(--fig);font-size:11px;fill:var(--ink-3)}
.flag{font-family:var(--fig);font-size:11px;fill:var(--flag);font-weight:500}
.cell{font-family:var(--fig);font-size:11px;fill:var(--ink)}
.cell.hi{fill:#fff}
.axlab{font-family:var(--body);font-size:11px;fill:var(--ink-2)}
.c1{fill:var(--c1)} .c2{fill:var(--c2)} .c3{fill:var(--c3)} .c4{fill:var(--c4)}
.quad{fill:var(--quad)}
.lane{stroke:var(--rule);stroke-width:1}
.quadlab{font-family:var(--body);font-size:11px;fill:var(--ink-2)}
.pt{fill:var(--ink-3);fill-opacity:.38}
.pt.gap{fill:var(--ord5);fill-opacity:.9}
.plab{font-family:var(--body);font-size:10px;fill:var(--ink-3)}
.plab.on{fill:var(--ink);font-weight:500}
.legend{display:flex;flex-wrap:wrap;gap:17px;margin:0 0 13px;font-size:12px;color:var(--ink-2)}
.legend span{display:flex;align-items:center;gap:6px}
.legend i{width:13px;height:13px;border-radius:3px;display:inline-block}
table.fx{border-collapse:collapse;width:100%;min-width:600px;font-size:13px}
table.fx th{text-align:left;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3);font-weight:500;padding:0 14px 7px 0;border-bottom:1px solid var(--rule)}
table.fx td{padding:7px 14px 7px 0;border-bottom:1px solid var(--rule);
  font-family:var(--fig);font-size:12.5px;color:var(--ink)}
table.fx td:first-child{font-family:var(--body);font-size:13.5px}
table.fx tr:last-child td{border-bottom:0}
.num{text-align:right}
.rec{background:var(--panel);border:1px solid var(--s1);border-radius:9px;padding:20px 22px;
  margin:0 0 30px}
.rec h3{font-family:var(--display);font-size:21px;margin:0 0 7px;font-weight:600}
.rec ol{margin:0;padding-left:20px}
.rec li{margin:0 0 7px;color:var(--ink-2)}
.rec li strong{color:var(--ink)}
hr.sep{border:0;border-top:1px solid var(--rule);margin:36px 0 26px}
@media (max-width:620px){
  h1{font-size:26px} h2{font-size:21px} .panel{padding:16px 14px 13px}
  .chart{min-width:720px}
}
"""

HTML = f"""<title>Opportunities Rebuilt</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&family=EB+Garamond:wght@500;600&display=swap">
<style>{CSS}</style>

<div class="wrap">
  <h1>Opportunities, rebuilt</h1>
  <p class="sub">Four options across the tab&rsquo;s two sections. <em>Highest scoring</em>
  draws a composite it never shows the parts of; <em>Program candidates</em> is a table
  with no chart at all, and it is the one section on the dashboard that is meant to
  change what someone does.</p>
  <p class="meta">Every figure here is recomputed from the committed JSON by
  <code>scripts/_oppfacts.py</code>. No query was run. Benchmark: {LW}, {money(LWA)} a year.
  Screen at its defaults: {MIN}+ openings, sub-baccalaureate and bachelor&rsquo;s.</p>

  <p class="part">Section one &middot; Highest scoring</p>

  <div class="panel">
    <h3>The problem: one number, four different things</h3>
    <p class="cap">The score is the mean of four percentile ranks — employment, growth,
    advertising, pay — at 25% each. The bar shows the mean. The four ranks are on the
    hover, which means the chart&rsquo;s argument is in a tooltip.</p>
    <div class="cwrap"><table class="fx">
      <tr><th>Occupation</th><th class="num">Score</th><th class="num">Employment</th>
          <th class="num">Growth</th><th class="num">Advertising</th><th class="num">Pay</th>
          <th class="num">Widest gap</th></tr>
      {"".join(
        f'<tr><td>{r["n"]}</td><td class="num">{r["sc"]:.1f}</td>'
        f'<td class="num">{r["s_size"]:.0f}</td><td class="num">{r["s_growth"]:.0f}</td>'
        f'<td class="num">{r["s_postings"]:.0f}</td><td class="num">{r["s_pay"]:.0f}</td>'
        f'<td class="num">{spread(r):.0f}</td></tr>'
        for r in [rn, cna] + sorted(TOP[:30], key=lambda r: -spread(r))[:3])}
    </table></div>
    <div class="note"><strong>Registered Nurses score {rn["sc"]:.1f} and Computer Network
    Architects {cna["sc"]:.1f}.</strong> Two points apart, and nothing alike: nursing is
    the {rn["s_size"]:.0f}th percentile for size and the {rn["s_growth"]:.0f}th for growth;
    network architects are the {cna["s_size"]:.0f}th for size and the
    {cna["s_growth"]:.0f}th for growth. One is a large occupation that is not growing
    much, the other is a small one growing fast. A reader who stops at the bar cannot
    tell them apart, and the two call for completely different responses.</div>
    {srcblock(
      "Vermont occupation data, 2025 · mean of four percentile ranks at " + str(F["weightEach"]) +
      "% each · occupations with &ge;" + str(F["minJobs"]) + " jobs (" + fmt(F["nEligible"]) + " of 796)",
      [("Score and its four parts", "data/sow.json → opp.top[].sc, .s_size, .s_growth, .s_postings, .s_pay"),
       ("Built by", "scripts/build_sow.py"),
       ("Upstream", "Lightcast Vermont occupation export — employment, projection to 2030, postings; BLS OEWS 2025 median pay"),
       ("Weighting", "25% each, equal by default. The SOW assigns the weights to VSCS, so they are a decision, not a finding.")])}
  </div>

  <div class="opt">
    <span class="tag">Option A</span>
    <h2>The score, unpacked</h2>
    <p class="sub">The bar stays the score, so the ranking is unchanged. The segments are
    where it came from — each of the four ranks contributing up to a quarter of the
    length.</p>
  </div>

  <div class="panel">
    <h3>Which occupations combine scale, growth, demand and pay?</h3>
    <p class="cap">Each bar is the opportunity score, split into the four percentile ranks
    averaged to make it. A bar of four even segments is an occupation strong on everything;
    a lopsided one is strong on something and weak on something else. The figure beside a
    lopsided bar is the distance between its best and worst rank.</p>
    <div class="legend">
      {"".join(f'<span><i style="background:var(--c{i + 1})"></i>{lab}</span>'
               for i, (_, lab) in enumerate(COMPS))}
    </div>
    <div class="cwrap">{chart_a()}</div>
    <div class="note">{wide["n"]} scores {wide["sc"]:.1f} out of ranks running
    <strong>{min(wide[k] for k, _ in COMPS):.0f} to {max(wide[k] for k, _ in COMPS):.0f}</strong>.
    Software Developers scores {TOP[0]["sc"]:.1f} out of
    {min(TOP[0][k] for k, _ in COMPS):.0f} to {max(TOP[0][k] for k, _ in COMPS):.0f}. The
    first is a bet on one thing; the second is strong on all four, and the current chart
    draws them as nearly the same kind of bar.</div>
    {srcblock(
      "Vermont occupation data, 2025 · mean of four percentile ranks at " + str(F["weightEach"]) +
      "% each · each segment is that rank divided by four · occupations with &ge;" +
      str(F["minJobs"]) + " jobs",
      [("Figures", "data/sow.json → opp.top[] — unchanged, only drawn differently"),
       ("Employment and growth", "Lightcast Vermont occupation export, 2025 and the 2030 projection"),
       ("Advertising", "Lightcast postings per 100 jobs"),
       ("Pay", "BLS OEWS 2025 median"),
       ("Built by", "scripts/build_sow.py")])}
  </div>

  <div class="opt">
    <span class="tag">Option B</span>
    <h2>The four ranks as a grid</h2>
    <p class="sub">The same four numbers, but readable down a column as well as across a
    row — so &ldquo;which of these is actually growing&rdquo; is one glance rather than
    fourteen hovers.</p>
  </div>

  <div class="panel">
    <h3>What is each high scorer strong at?</h3>
    <p class="cap">One row per occupation, one column per component, shaded by percentile
    rank on the same five-step scale the concentration grid and the Overview use. The last
    column is the distance between an occupation&rsquo;s best and worst rank, which is how
    much the single score is hiding.</p>
    <div class="legend">
      <span><i style="background:var(--ord1)"></i>Under 20th percentile</span>
      <span><i style="background:var(--ord3)"></i>40th to 60th</span>
      <span><i style="background:var(--ord5)"></i>80th and over</span>
    </div>
    <div class="cwrap">{chart_b()}</div>
    <div class="note">Read down the <em>Employment</em> column and the list splits in two:
    the occupations that are already large, and the ones scoring on growth and advertising
    from a small base. Both are legitimate answers to &ldquo;worth paying attention
    to&rdquo; and they are not the same bet.</div>
    {srcblock(
      "Vermont occupation data, 2025 · four percentile ranks per occupation · "
      "occupations with &ge;" + str(F["minJobs"]) + " jobs (" + fmt(F["nEligible"]) + " of 796)",
      [("Figures", "data/sow.json → opp.top[].s_size, .s_growth, .s_postings, .s_pay"),
       ("Shading", "the --ord1…--ord5 ramp, five even steps of percentile rank"),
       ("Built by", "scripts/build_sow.py"),
       ("Note", "a rank, not a rate: 96 means 96% of scored occupations rank lower on that measure, not 96% of anything")])}
  </div>

  <p class="part">Section two &middot; Program candidates</p>

  <div class="panel">
    <h3>The problem: the one section meant to change a decision has no chart</h3>
    <p class="cap">A screen rather than a ranking — openings, pay, a credential VSCS
    awards, and optionally excluding the obvious — producing {len(CAND)} occupations at
    the default settings. It is a sortable table and nothing else.</p>
    <div class="cwrap"><table class="fx">
      <tr><th>Pipeline</th><th class="num">Occupations</th>
          <th class="num">Openings a year between them</th></tr>
      {"".join(
        f'<tr><td>{p}</td><td class="num">{len([r for r in CAND if r["pipeline"] == p])}</td>'
        f'<td class="num">{fmt(sum(r["o"] for r in CAND if r["pipeline"] == p))}</td></tr>'
        for p in PIPE)}
    </table></div>
    <div class="note">The table carries the finding and does not show it:
    <strong>{nNone} of the {len(CAND)} occupations that clear the screen have no VSCS
    pipeline at all</strong>, and another {nThin} have a thin one. That is the answer to
    &ldquo;which occupations could VSCS act on&rdquo;, and it is currently a column a
    reader has to sort by to notice.</div>
    {srcblock(
      "Vermont occupation data, 2025, against federal completions data, 2024 · openings &ge; " +
      str(MIN) + "/yr · pay at or above " + money(LWA) + " · sub-baccalaureate and "
      "bachelor&rsquo;s · excluding the 25 largest occupations",
      [("The screen", "lib/screen.js opportunityScreen(), computed in the browser so the controls move it"),
       ("Occupations, openings, pay, growth", "data/lightcast.json → allOcc[]"),
       ("Graduates attributed", "data/sow.json → vscs.bySoc[].linked, .ratio"),
       ("Built by", "scripts/build.py, scripts/build_sow.py"),
       ("The allocation", "CIP-to-SOC is many-to-many, so each program&rsquo;s completions are split across its linked occupations in proportion to Vermont employment. A model of where graduates go, not an observation.")])}
  </div>

  <div class="opt">
    <span class="tag">Option C</span>
    <h2>Demand against pipeline</h2>
    <p class="sub">The two numbers the section exists to compare, on two axes. Everything
    in the shaded band is work that is hiring and that VSCS produces almost nobody for.</p>
  </div>

  <div class="panel">
    <h3>Where is Vermont hiring that VSCS does not supply?</h3>
    <p class="cap">One point per occupation clearing the screen, placed by annual openings
    and sorted into three lanes by how much VSCS already produces for it. Point size is
    employment. Pipeline is three states rather than a number — sixteen of these
    occupations have exactly no graduates attributed — so it is a lane rather than an
    axis, and the shaded lane is the one the section exists to find.</p>
    <div class="legend">
      <span><i style="background:var(--ord5)"></i>No VSCS pipeline</span>
      <span><i style="background:var(--ink-3);opacity:.45"></i>Thin or established</span>
      <span><i style="background:var(--quad)"></i>The lane with nothing behind it</span>
    </div>
    <div class="cwrap">{chart_c()}</div>
    <div class="note"><strong>{nNone} of the {len(CAND)} occupations clearing the screen
    have no VSCS pipeline at all, and they carry {fmt(noneOpen)} openings a year between
    them</strong> — {", ".join(short(r["n"], 34) for r in noneTop[:3])} among them. Read
    across that lane and the point is how far right it reaches: this is not a tail of
    small occupations, it is some of the hardest hiring on the list. None of it says VSCS
    should start a program — the scope of this work stops short of that, and no pipeline
    can be the right answer — it says where to look.</div>
    {srcblock(
      "Vermont occupation data, 2025, against federal completions data, 2024 · "
      + str(len(CAND)) + " occupations clearing the screen · lanes are none, under 8% of the "
      "occupation&rsquo;s openings, and above it · benchmark " + money(LWA) + " a year (" + LW + ")",
      [("Openings and employment", "data/lightcast.json → allOcc[].o, .j"),
       ("Graduates attributed", "data/sow.json → vscs.bySoc[].linked — CCV and Vermont State University completions, 2024, allocated across linked occupations"),
       ("The screen itself", "lib/screen.js opportunityScreen()"),
       ("Built by", "scripts/build.py, scripts/build_sow.py"),
       ("Caveat", "&ldquo;graduates attributed&rdquo; is a modelled split, not a headcount of people who took that job. An occupation with none may still be served by a program this crosswalk does not link.")])}
  </div>

  <div class="opt">
    <span class="tag">Option D</span>
    <h2>The screen, ranked</h2>
    <p class="sub">Closer to what is there now: the same list in the same order, but with
    the pipeline carried by the bar instead of spelled out in a column, and the signals as
    a mark rather than a count.</p>
  </div>

  <div class="panel">
    <h3>Which occupations could VSCS act on?</h3>
    <p class="cap">Occupations clearing all four tests, most openings first. The bar is
    annual openings and its shade is how much VSCS already produces for that work.
    Signals counts how many of three things an occupation has going for it — openings,
    advertising and projected growth — each judged against others needing the same
    credential.</p>
    <div class="legend">
      <span><i style="background:var(--ord5)"></i>No VSCS pipeline</span>
      <span><i style="background:var(--ord3)"></i>Thin pipeline</span>
      <span><i style="background:var(--ord1)"></i>Established pipeline</span>
    </div>
    <div class="cwrap">{chart_d()}</div>
    <div class="note">Shading by pipeline rather than ranking by it keeps the order the
    reader expects — biggest hiring first — while making the gap visible without a sort.
    The darkest bars near the top are the section&rsquo;s whole argument.</div>
    {srcblock(
      "Vermont occupation data, 2025, against federal completions data, 2024 · thresholds "
      "set on the controls · a candidate for investigation, not a recommendation",
      [("Figures", "the existing screen, unchanged — lib/screen.js opportunityScreen()"),
       ("Openings", "data/lightcast.json → allOcc[].o — Lightcast 2021–2025 openings ÷ 4"),
       ("Pipeline", "data/sow.json → vscs.bySoc[].linked and .ratio, thin below 8%"),
       ("Signals", "openings and postings per 100 jobs against the median for the same credential; growth above 3%"),
       ("Built by", "scripts/build.py, scripts/build_sow.py")])}
  </div>

  <hr class="sep">

  <div class="rec">
    <h3>What I would build</h3>
    <ol>
      <li><strong>Option A for Highest scoring.</strong> It keeps the ranking and the
      score exactly as they are and costs nothing to read — the bar still means what it
      meant — while putting the argument on the chart instead of in a tooltip. Option B is
      the better analytical object but it is a grid of fourteen rows of numbers, which is
      a heavier thing to open a section with.</li>
      <li><strong>Option C for Program candidates</strong>, with the table kept underneath
      as <em>Show the figures</em>. This is the one section on the dashboard meant to
      change what someone does, and the comparison it exists to make — hiring against what
      VSCS already produces — is currently two columns a reader has to hold in their head.
      Option D is the safer change and the weaker one: it shades a ranking that is still
      ranked by openings, so the gap is visible but not measured.</li>
      <li><strong>Click-through on both</strong>, the way Pathways and the Overview now
      carry it: a pane beside the chart with that occupation&rsquo;s figures and the
      others in its group, and a link through to the full table.</li>
      <li><strong>One thing to decide first.</strong> The score weights are equal because
      nobody has set them. The SOW assigns that choice to VSCS, and Option A makes the
      consequence visible for the first time — four segments a reader can see are equal.
      Worth asking whether they should be.</li>
    </ol>
  </div>
</div>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="").write(HTML)
print("wrote", os.path.abspath(OUT), len(HTML), "bytes")
