"""Writes the "Which credentials pay" prototype page. Throwaway.

Three ways to draw the section that is a table today, in the dashboard's own
visual language. Every figure comes out of _doorfacts.py, which recomputes them
from the committed JSON -- no query is run.
"""
import io
import json
import math
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(io.open(os.path.join(HERE, "_doorfacts.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "..", "_shots", "which-credentials-pay.html")

ROWS = F["rows"]
ORDER = F["order"]
R = {r["t"]: r for r in ROWS}
LWA = F["lwa"]
MIN = F["minOpen"]
PTS = F["pts"]


def money(v):
    return "$" + format(int(round(v)), ",")


def fmt(v):
    return format(int(round(v)), ",")


def short(n, w=26):
    """A point label that fits, cut at a word rather than mid-word."""
    if len(n) <= w:
        return n
    cut = n[:w].rsplit(" ", 1)[0]
    return (cut or n[:w]) + "…"


# ---------------------------------------------------------------- chart A ---
# The funnel as nested bars over a shared count of occupations.
def chart_a():
    W, padL, plotW, padT, rowH = 1180, 206, 660, 54, 72
    H = padT + len(ORDER) * rowH + 18
    mx = max(r["nAll"] for r in ROWS)
    X = lambda n: n / mx * plotW
    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Occupations at each '
         'credential that hire in volume and pay a living wage">' % (W, H)]
    for t in (100, 200, 300):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (padL + X(t), padT - 12, padL + X(t), padT + len(ORDER) * rowH - 26))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%d</text>'
                 % (padL + X(t), padT - 20, t))
    s.append('<text class="colhead" x="1176" y="%d" text-anchor="end">OPENINGS THAT PAY</text>'
             % (padT - 20))
    for i, t in enumerate(ORDER):
        r = R[t]
        y = padT + i * rowH
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 14, y + 22, t))
        s.append('<rect class="f1" x="%d" y="%d" width="%.1f" height="30" rx="3"/>'
                 % (padL, y + 2, X(r["nAll"])))
        s.append('<rect class="f2" x="%d" y="%d" width="%.1f" height="30" rx="3"/>'
                 % (padL, y + 2, X(r["nHiring"])))
        s.append('<rect class="f3" x="%d" y="%d" width="%.1f" height="30" rx="3"/>'
                 % (padL, y + 2, max(2, X(r["nPaying"]))))
        s.append('<text class="vlab" x="%.1f" y="%d">%d of %d</text>'
                 % (padL + X(r["nAll"]) + 11, y + 22, r["nPaying"], r["nAll"]))
        s.append('<text class="fig" x="1176" y="%d" text-anchor="end">%s of %s</text>'
                 % (y + 18, fmt(r["openPay"]), fmt(r["openAll"])))
        s.append('<text class="figsub" x="1176" y="%d" text-anchor="end">%.0f%%</text>'
                 % (y + 35, r["shareOpen"]))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart B ---
# The same screen counted in openings rather than in doors, and read off the pay
# distributions rather than through a median gate.
def chart_b():
    W, padL, plotW, padT, rowH = 1180, 206, 700, 54, 66
    H = padT + len(ORDER) * rowH + 14
    mx = max(r["openAll"] for r in ROWS)
    X = lambda n: n / mx * plotW
    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Annual openings at each '
         'credential, split by whether the work pays a living wage">' % (W, H)]
    for t in (5000, 10000, 15000):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (padL + X(t), padT - 12, padL + X(t), padT + len(ORDER) * rowH - 24))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%s</text>'
                 % (padL + X(t), padT - 20, fmt(t / 1000) + "k"))
    s.append('<text class="colhead" x="1176" y="%d" text-anchor="end">THAT PAY</text>' % (padT - 20))
    for i, t in enumerate(ORDER):
        r = R[t]
        y = padT + i * rowH
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 14, y + 21, t))
        s.append('<rect class="f1" x="%d" y="%d" width="%.1f" height="28" rx="3"/>'
                 % (padL, y + 2, X(r["openAll"])))
        s.append('<rect class="f3" x="%d" y="%d" width="%.1f" height="28" rx="3"/>'
                 % (padL, y + 2, X(r["wOpen"])))
        s.append('<text class="vlab" x="%.1f" y="%d">%s of %s</text>'
                 % (padL + X(r["openAll"]) + 11, y + 21, fmt(r["wOpen"]), fmt(r["openAll"])))
        s.append('<text class="fig" x="1176" y="%d" text-anchor="end">%.0f%%</text>'
                 % (y + 21, r["wShare"]))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart C ---
# Every occupation at its own openings and its own pay, five facets sharing axes.
def facets():
    FW, FH = 352, 258
    padL, padB, padT, padR = 44, 30, 26, 10
    pw, ph = FW - padL - padR, FH - padT - padB
    XMIN, XMAX = 5.0, 2200.0
    YMIN, YMAX = 25000.0, 180000.0

    def X(v):
        v = max(XMIN, min(XMAX, v))
        return padL + (math.log10(v) - math.log10(XMIN)) / (
            math.log10(XMAX) - math.log10(XMIN)) * pw

    def Y(v):
        v = max(YMIN, min(YMAX, v))
        return padT + ph - (v - YMIN) / (YMAX - YMIN) * ph

    out = []
    for ti, t in enumerate(ORDER):
        r = R[t]
        mine = [p for p in PTS if p[0] == ti]
        s = ['<svg class="facet" viewBox="0 0 %d %d" role="img" aria-label="%s: openings '
             'against pay, one point per occupation">' % (FW, FH, t)]
        # the quadrant that passes both screens
        s.append('<rect class="quad" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/>'
                 % (X(MIN), padT, padL + pw - X(MIN), Y(LWA) - padT))
        for gv in (10, 100, 1000):
            s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%.1f"/>'
                     % (X(gv), padT, X(gv), padT + ph))
            s.append('<text class="ftick" x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                     % (X(gv), padT + ph + 15, fmt(gv)))
        for gv in (50000, 100000, 150000):
            s.append('<line class="grid" x1="%d" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                     % (padL, Y(gv), padL + pw, Y(gv)))
            s.append('<text class="ftick" x="%d" y="%.1f" text-anchor="end">$%dk</text>'
                     % (padL - 6, Y(gv) + 3, gv // 1000))
        for p in mine:
            _, o, m, j, n = p
            ok = o >= MIN and m >= LWA
            s.append('<circle class="%s" cx="%.1f" cy="%.1f" r="%.1f"/>'
                     % ("pt on" if ok else "pt", X(o), Y(m), 2.4 + min(3.4, (j or 0) ** 0.42 / 11)))
        # the two screens
        s.append('<line class="rule" x1="%.1f" y1="%d" x2="%.1f" y2="%.1f"/>'
                 % (X(MIN), padT, X(MIN), padT + ph))
        s.append('<line class="rule" x1="%d" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (padL, Y(LWA), padL + pw, Y(LWA)))
        # name the biggest that clears, and the biggest that does not
        lab = []
        if r["top"]:
            lab.append((r["top"][0], True))
        if r["miss"]:
            lab.append((r["miss"][0], False))
        for o, good in lab:
            x, y = X(o["o"]), Y(o["m"])
            anchor = "end" if x > padL + pw * 0.58 else "start"
            dx = -7 if anchor == "end" else 7
            s.append('<text class="plab%s" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                     % (" on" if good else "", x + dx, y + (-9 if good else 15),
                        anchor, short(o["n"])))
        s.append('<text class="ftitle" x="%d" y="%d">%s</text>' % (padL, 15, t))
        s.append('<text class="fsub" x="%.1f" y="%d" text-anchor="end">%d of %d clear both</text>'
                 % (padL + pw, 15, r["nPaying"], r["nAll"]))
        s.append("</svg>")
        out.append('<div class="fcell">%s</div>' % "\n".join(s))
    return '<div class="fgridc">%s</div>' % "".join(out)


# -------------------------------------------------------------------- page ---
def srcblock(line, uses):
    rows = "".join("<tr><th>%s</th><td>%s</td></tr>" % (a, b) for a, b in uses)
    return ('<p class="src">%s</p>'
            '<details class="uses"><summary>What this chart uses</summary>'
            '<table>%s</table></details>' % (line, rows))


LW = F["lw"]
nf, hs, sb, ba, gr = (R[t] for t in ORDER)
nf_miss = sum(o["o"] for o in nf["miss"])

CSS = r"""
:root{
  --s1:#009ba5; --ord1:#ccebed; --ord2:#99d7db; --ord3:#66c3c9; --ord4:#33afb7; --ord5:#009ba5;
  --ink:#16202a; --ink-2:#41505e; --ink-3:#74838f;
  --bg:#f7f8f8; --panel:#fff; --rule:#e4e8ea; --rule-2:#cfd6da; --track:#e8ecee; --cool:#e9f5f6;
  --quad:#ddf1f2;
  --display:'EB Garamond',Georgia,serif;
  --body:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --fig:'DM Mono',ui-monospace,'SF Mono',Menlo,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#eef2f4; --ink-2:#b4c0c8; --ink-3:#8a97a1;
  --bg:#11171c; --panel:#19212a; --rule:#273139; --rule-2:#36434d; --track:#222c35; --cool:#14313a;
  --quad:#16343a;
  --s1:#33afb7; --ord1:#0f3a3f; --ord2:#15606a; --ord3:#008c9b; --ord4:#33afb7; --ord5:#66c3c9;
  color-scheme:dark;
}}
:root[data-theme="dark"]{
  --ink:#eef2f4; --ink-2:#b4c0c8; --ink-3:#8a97a1;
  --bg:#11171c; --panel:#19212a; --rule:#273139; --rule-2:#36434d; --track:#222c35; --cool:#14313a;
  --quad:#16343a;
  --s1:#33afb7; --ord1:#0f3a3f; --ord2:#15606a; --ord3:#008c9b; --ord4:#33afb7; --ord5:#66c3c9;
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
.tick,.ftick{font-family:var(--fig);font-size:10px;fill:var(--ink-3)}
.colhead{font-family:var(--body);font-size:10px;letter-spacing:.09em;fill:var(--ink-3);font-weight:500}
.clab{font-family:var(--body);font-size:13px;fill:var(--ink)}
.vlab{font-family:var(--fig);font-size:12px;fill:var(--ink);font-weight:500}
.fig{font-family:var(--fig);font-size:12.5px;fill:var(--ink);font-weight:500}
.figsub{font-family:var(--fig);font-size:11px;fill:var(--ink-3)}
.f1{fill:var(--track)}
.f2{fill:var(--ord3)}
.f3{fill:var(--ord5)}
.rule{stroke:var(--ink-2);stroke-width:1.2;stroke-dasharray:4 3}
.quad{fill:var(--quad)}
.pt{fill:var(--ink-3);fill-opacity:.3}
.pt.on{fill:var(--ord5);fill-opacity:.85}
.plab{font-family:var(--body);font-size:9.5px;fill:var(--ink-3)}
.plab.on{fill:var(--ink);font-weight:500}
.ftitle{font-family:var(--body);font-size:12px;fill:var(--ink);font-weight:500}
.fsub{font-family:var(--fig);font-size:10px;fill:var(--ink-3)}
.fgridc{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(310px,1fr))}
.fcell{border:1px solid var(--rule);border-radius:7px;padding:4px;min-width:0}
.facet{width:100%;height:auto;display:block}
.legend{display:flex;flex-wrap:wrap;gap:17px;margin:0 0 13px;font-size:12px;color:var(--ink-2)}
.legend span{display:flex;align-items:center;gap:6px}
.legend i{width:13px;height:13px;border-radius:3px;display:inline-block}
table.fx{border-collapse:collapse;width:100%;min-width:620px;font-size:13px}
table.fx th{text-align:left;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3);font-weight:500;padding:0 14px 7px 0;border-bottom:1px solid var(--rule)}
table.fx td{padding:7px 14px 7px 0;border-bottom:1px solid var(--rule);
  font-family:var(--fig);font-size:12.5px;color:var(--ink)}
table.fx td:first-child{font-family:var(--body);font-size:13.5px}
table.fx tr:last-child td{border-bottom:0}
.num{text-align:right}
.was{color:var(--ink-3)}
.rec{background:var(--panel);border:1px solid var(--s1);border-radius:9px;padding:20px 22px;
  margin:0 0 30px}
.rec h3{font-family:var(--display);font-size:21px;margin:0 0 7px;font-weight:600}
.rec ol{margin:0;padding-left:20px}
.rec li{margin:0 0 7px;color:var(--ink-2)}
.rec li strong{color:var(--ink)}
hr.sep{border:0;border-top:1px solid var(--rule);margin:40px 0 28px}
@media (max-width:620px){
  h1{font-size:26px} h2{font-size:21px} .panel{padding:16px 14px 13px}
  .chart{min-width:680px}
}
"""

HTML = f"""<title>Which Credentials Pay</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&family=EB+Garamond:wght@500;600&display=swap">
<style>{CSS}</style>

<div class="wrap">
  <h1>Which credentials pay</h1>
  <p class="sub">Three ways to draw the Pathways section that is a plain table today.
  It screens every Vermont occupation twice — hiring in volume, then paying a living
  wage — and prints the counts. Drawing it is the easy part; the question is which of
  three different questions the section should be asking.</p>
  <p class="meta">Every figure here is recomputed from the committed JSON by
  <code>scripts/_doorfacts.py</code>. No query was run. Benchmark: {LW}, {money(LWA)} a
  year. Volume screen: {MIN}+ openings a year.</p>

  <div class="panel">
    <h3>What the table says now</h3>
    <p class="cap">The same five rows the section prints today, plus the two columns it
    does not have.</p>
    <div class="cwrap"><table class="fx">
      <tr><th>Entry credential</th><th class="num">Occupations</th>
          <th class="num">Hiring {MIN}+</th><th class="num">And paying</th>
          <th class="num">Openings a year</th><th class="num">In work that pays</th>
          <th class="num">Share</th></tr>
      {"".join(
        f'<tr><td>{r["t"]}</td><td class="num">{r["nAll"]}</td>'
        f'<td class="num">{r["nHiring"]}</td><td class="num">{r["nPaying"]}</td>'
        f'<td class="num">{fmt(r["openAll"])}</td><td class="num">{fmt(r["openPay"])}</td>'
        f'<td class="num">{r["shareOpen"]:.0f}%</td></tr>' for r in ROWS)}
    </table></div>
    <div class="note"><strong>The screen changes meaning as you go up the ladder.</strong>
    At the bottom the pay test is what bites: {nf["nHiring"]} no-credential occupations hire
    in volume and <strong>{nf["nPaying"]}</strong> of them pay. At the top the volume test is:
    only {gr["nHiring"]} of {gr["nAll"]} graduate occupations hire {MIN}+ a year, and all
    {gr["nPaying"]} of those pay. So &ldquo;{gr["nPaying"]} of {gr["nAll"]}&rdquo; and
    &ldquo;{nf["nPaying"]} of {nf["nAll"]}&rdquo; are not failing the same test, and one
    number per row cannot say which.</div>
    {srcblock(
      "Vermont occupation data, 2025 · entry credential · openings &ge; " + str(MIN) +
      "/yr · occupation median against the benchmark · benchmark " + money(LWA) + " a year (" + LW + ")",
      [("Occupations and credential", "data/lightcast.json → allOcc[].t, .n"),
       ("Openings", "data/lightcast.json → allOcc[].o — Lightcast 2021–2025 openings ÷ 4"),
       ("Median pay", "data/lightcast.json → allOcc[].m (BLS OEWS 2025 median)"),
       ("Benchmark", "data/lightcast.json → livingWage (MIT Living Wage, Vermont 2025)"),
       ("Built by", "scripts/build.py, scripts/get_lw.py"),
       ("Computed in app", "lib/data.js credentialFunnel()")])}
  </div>

  <hr class="sep">

  <div class="opt">
    <span class="tag">Option A</span>
    <h2>The funnel, drawn</h2>
    <p class="sub">The table as it stands, made visual. Each rung narrows twice, and the
    narrowing is the finding.</p>
  </div>

  <div class="panel">
    <h3>Which credentials lead to work that both hires and pays?</h3>
    <p class="cap">Every Vermont occupation at each entry credential, narrowed twice: to
    those hiring at least {MIN} a year, and then to those whose typical job pays a living
    wage. Counts of occupations, not of jobs, so it reads as how many doors a credential
    opens. The right column converts the same screen into annual openings.</p>
    <div class="legend">
      <span><i style="background:var(--track)"></i>All occupations</span>
      <span><i style="background:var(--ord3)"></i>Hiring {MIN}+ a year</span>
      <span><i style="background:var(--ord5)"></i>And paying a living wage</span>
    </div>
    <div class="cwrap">{chart_a()}</div>
    <div class="note">At the bottom of the ladder the narrowing is severe:
    <strong>{nf["nPaying"]} of {nf["nAll"]}</strong> occupations requiring no formal
    credential clear both screens — {fmt(nf["openPay"])} of {fmt(nf["openAll"])} annual
    openings, or {nf["shareOpen"]:.0f}%.</div>
    {srcblock(
      "Vermont occupation data, 2025 · entry credential · openings &ge; " + str(MIN) +
      "/yr · occupation median against the benchmark · benchmark " + money(LWA) + " a year (" + LW + ")",
      [("Figures", "the table above, unchanged — this option changes only the form"),
       ("Occupations, openings, median pay", "data/lightcast.json → allOcc[].t, .o, .m"),
       ("Computed in app", "lib/data.js credentialFunnel()"),
       ("Caveat", "the pay screen is the occupation median against the benchmark — the median rule, used here on a question about the occupation rather than about its jobs, which is the one place it holds")])}
  </div>

  <div class="opt">
    <span class="tag">Option B</span>
    <h2>Openings, not doors</h2>
    <p class="sub">The same screen counted in the thing a person leaving a credential
    actually meets — a year's worth of openings — and measured off the pay distributions
    instead of through a median gate.</p>
  </div>

  <div class="panel">
    <h3>How much of a year&rsquo;s hiring at each credential pays a living wage?</h3>
    <p class="cap">Every annual opening at each entry credential, with the filled part
    being those in work paying at or above the benchmark. Read off each occupation&rsquo;s
    own pay distribution and weighted by its openings, so an occupation whose midpoint
    clears by a dollar contributes half its openings rather than all of them. No volume
    screen: an opening counts whether or not its occupation hires {MIN} a year.</p>
    <div class="legend">
      <span><i style="background:var(--ord5)"></i>Openings in work that pays a living wage</span>
      <span><i style="background:var(--track)"></i>The rest</span>
    </div>
    <div class="cwrap">{chart_b()}</div>
    <div class="note">Every figure rises, because the median gate was throwing away whole
    occupations over a few hundred dollars and discarding every small employer as well.
    No formal credential goes {nf["shareOpen"]:.0f}% &rarr;
    <strong>{nf["wShare"]:.0f}%</strong>, high school {hs["shareOpen"]:.0f}% &rarr;
    <strong>{hs["wShare"]:.0f}%</strong>, a bachelor&rsquo;s {ba["shareOpen"]:.0f}% &rarr;
    <strong>{ba["wShare"]:.0f}%</strong>. The ordering holds; the level does not, and the
    gated version is the one on the tab today.</div>
    {srcblock(
      "Vermont occupation data, 2025 · entry credential · the benchmark&rsquo;s position read "
      "off each occupation&rsquo;s own 10th-to-90th percentile ladder, weighted by its annual "
      "openings · benchmark " + money(LWA) + " a year (" + LW + ")",
      [("Openings and credential", "data/lightcast.json → allOcc[].o, .t"),
       ("Pay ladder", "data/percentiles.json → occ[].p10…p90 (BLS OEWS 2025, as published)"),
       ("Benchmark", "data/lightcast.json → livingWage (MIT Living Wage, Vermont 2025)"),
       ("Built by", "scripts/build.py, scripts/build_pct.py, scripts/get_lw.py"),
       ("Computed in app", "lib/wage.js shareBelow(), weighted by openings instead of by jobs — the same measure the Overview, Wage quality and the pay ladder use"),
       ("Not covered", "15 of 796 occupations carry no published ladder and drop out of both sides")])}
  </div>

  <div class="opt">
    <span class="tag">Option C</span>
    <h2>Which ones</h2>
    <p class="sub">The table says &ldquo;{nf["nPaying"]} of {nf["nAll"]}&rdquo; and stops,
    which is exactly where the reader&rsquo;s next question starts. One point per
    occupation, the two screens drawn as lines, and the corner that passes both shaded.</p>
  </div>

  <div class="panel">
    <h3>Where does each credential&rsquo;s work actually sit?</h3>
    <p class="cap">One point per occupation: openings a year across, typical pay up, point
    size is employment. The vertical line is the {MIN}-openings screen and the horizontal
    one is the living wage, so the shaded corner is the work that both hires in volume and
    pays. Same axes on all five, so the panels can be read against each other.</p>
    <div class="legend">
      <span><i style="background:var(--ord5)"></i>Clears both screens</span>
      <span><i style="background:var(--ink-3);opacity:.4"></i>Does not</span>
      <span><i style="background:var(--quad)"></i>The corner that passes</span>
    </div>
    {facets()}
    <div class="note">The four biggest doors at the bottom of the ladder all fail on pay,
    not on hiring: Fast Food and Counter Workers, Cashiers, Retail Salespersons and
    Janitors together carry <strong>{fmt(nf_miss)} openings a year</strong> — more than
    four times the {fmt(nf["openPay"])} in the three no-credential occupations that clear
    both screens. At the top the pattern inverts: the graduate panel is nearly empty on
    the left of the volume line, because its work is spread thin across
    {gr["nAll"]} occupations.</div>
    {srcblock(
      "Vermont occupation data, 2025 · 771 occupations carrying both an openings figure and "
      "a published median · log scale on openings · benchmark " + money(LWA) + " a year (" + LW + ")",
      [("One point per occupation", "data/lightcast.json → allOcc[].o (openings), .m (median pay), .j (employment, as point size), .t (which panel)"),
       ("Openings", "Lightcast 2021–2025 openings ÷ 4 — see Methods on that divisor"),
       ("Median pay", "BLS OEWS 2025, as published"),
       ("Built by", "scripts/build.py"),
       ("Points left out", "25 of 796 occupations report no openings or no median and cannot be placed")])}
  </div>

  <hr class="sep">

  <div class="rec">
    <h3>What I would build</h3>
    <ol>
      <li><strong>Option C as the section</strong>, with Option A on a measure chip beside
      it. C answers the question the table raises and A does not — which work, and whether
      a rung fails on hiring or on pay — and it is the only one of the three where the
      reader can see that the bottom of the ladder fails on pay while the top fails on
      volume.</li>
      <li><strong>Take Option B&rsquo;s measure regardless of the layout.</strong> The
      median gate is defensible for counting doors, which is what Option A does. It is not
      defensible for counting openings, and the tab prints an openings column today using
      it — {nf["shareOpen"]:.0f}% where the distributions say {nf["wShare"]:.0f}%. Either
      fix that column or drop it.</li>
      <li><strong>Keep the table.</strong> It is already under the chart as
      <em>Show the figures</em>, and it sorts and exports. Nothing here needs to replace
      it; the section just should not open with it.</li>
      <li><strong>One caveat to put in the copy:</strong> Waiters and Waitresses is one of
      the three no-credential occupations that clears the pay screen, at
      {money(nf["top"][0]["m"])}. That is an OEWS figure including tips, and
      {nf["top"][0]["below"]:.0f}% of its jobs still fall below the benchmark. It is the
      weakest point in the section and someone will find it.</li>
    </ol>
  </div>
</div>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="").write(HTML)
print("wrote", os.path.abspath(OUT), len(HTML), "bytes")
