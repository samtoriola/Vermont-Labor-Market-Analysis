"""Writes the VSCS alignment prototype page. Throwaway.

Every figure comes out of _vscsfacts2.py, which recomputes them from the
committed JSON -- no query is run.
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
F = json.load(io.open(os.path.join(HERE, "_vscsfacts2.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "..", "_shots", "vscs-alignment.html")

V = F["v"]
ROWS = F["rows"]
TOT_CRED, TOT_LINK = F["totCred"], F["totLink"]
BY_GAP = sorted(ROWS, key=lambda r: -(r["shareGrad"] - r["shareOpen"]))


def fmt(v):
    return format(int(round(v)), ",")


def short(n, w=30):
    if len(n) <= w:
        return n
    cut = n[:w].rsplit(" ", 1)[0]
    return (cut or n[:w]) + "…"


# ---------------------------------------------------------------- chart A ---
# Four figures on one scale. The point is the proportion between them, so they
# must not each get an axis of their own.
def chart_a():
    W, padL, plotW, padT, rowH = 1180, 330, 620, 48, 62
    stages = [
        ("Openings a year in Vermont", V["openAll"], "--ord1", None),
        ("Asking for a credential VSCS awards", V["openCred"], "--ord3",
         "%.0f%% of them" % (V["openCred"] / V["openAll"] * 100)),
        ("VSCS completions, 2024", V["totalCompletions"], "--ord5", None),
        ("Landing in a Vermont occupation", TOT_LINK, "--ord5",
         "%.0f%% of completions" % (TOT_LINK / V["totalCompletions"] * 100)),
    ]
    H = padT + len(stages) * rowH + 62
    mx = float(V["openAll"])
    X = lambda v: v / mx * plotW
    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="VSCS completions '
         'against Vermont openings, on one scale">' % (W, H)]
    for t in (10000, 20000, 30000, 40000):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (padL + X(t), padT - 12, padL + X(t), padT + len(stages) * rowH - 16))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%dk</text>'
                 % (padL + X(t), padT - 20, t // 1000))
    for i, (lab, v, col, sub) in enumerate(stages):
        y = padT + i * rowH
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 16, y + 23, lab))
        s.append('<rect x="%d" y="%d" width="%.1f" height="30" rx="3" fill="var(%s)"/>'
                 % (padL, y + 3, max(2.5, X(v)), col))
        s.append('<text class="vlab" x="%.1f" y="%d">%s</text>'
                 % (padL + max(2.5, X(v)) + 11, y + 24, fmt(v)))
        if sub:
            s.append('<text class="figsub" x="%.1f" y="%d">%s</text>'
                     % (padL + max(2.5, X(v)) + 11 + len(fmt(v)) * 7.6 + 12, y + 24, sub))
    # the comparison the tab exists to make, drawn as a bracket between rows 2 and 4
    y2 = padT + 1 * rowH + 18
    y4 = padT + 3 * rowH + 18
    bx = padL + X(V["openCred"]) + 150
    s.append('<path class="brk" d="M%.1f %d H%.1f V%d H%.1f V%d"/>'
             % (bx - 6, y2, bx, y4, bx - 6, y4))
    s.append('<text class="brklab" x="%.1f" y="%.1f">%.1f%% &#8212; graduates against the '
             'openings that ask for them</text>'
             % (bx + 9, (y2 + y4) / 2 + 4, TOT_LINK / TOT_CRED * 100))
    s.append('<text class="figsub" x="%d" y="%d">Against ALL openings it reads %.1f%%, '
             'which is what the tab shows today.</text>'
             % (padL, H - 16, TOT_LINK / sum(r["openAll"] for r in ROWS) * 100))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart B ---
# Two shares of two different totals, which is what makes them comparable.
def chart_b():
    W, padL, plotW, padT, rowH = 1180, 300, 600, 56, 31
    H = padT + len(BY_GAP) * rowH + 18
    mx = 35.0
    X = lambda v: padL + v / mx * plotW
    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Share of VSCS '
         'graduates against share of credential-requiring openings, by occupation group">'
         % (W, H)]
    for t in (0, 10, 20, 30):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (X(t), padT - 12, X(t), padT + len(BY_GAP) * rowH - 10))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%d%%</text>'
                 % (X(t), padT - 20, t))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">GRADUATES</text>'
             % (W - 92, padT - 20))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">GAP</text>'
             % (W - 4, padT - 20))
    for i, r in enumerate(BY_GAP):
        y = padT + i * rowH + 15
        a, b = X(r["shareGrad"]), X(r["shareOpen"])
        gap = r["shareGrad"] - r["shareOpen"]
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 16, y + 4, short(r["f"], 40)))
        s.append('<line class="conn %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % ("up" if gap > 0 else "dn", a, y, b, y))
        s.append('<circle class="dOpen" cx="%.1f" cy="%.1f" r="5"/>' % (b, y))
        s.append('<circle class="dGrad" cx="%.1f" cy="%.1f" r="5"/>' % (a, y))
        s.append('<text class="fig" x="%d" y="%d" text-anchor="end">%.1f</text>'
                 % (W - 92, y + 4, r["linked"]))
        # Three groups have no graduates and no credential-requiring openings, so
        # the gap is a rounding artefact. "-0.0 pts" is not a figure.
        s.append('<text class="%s" x="%d" y="%d" text-anchor="end">%s pts</text>'
                 % ("flag" if abs(gap) >= 5 else "figsub", W - 4, y + 4,
                    "0.0" if abs(gap) < 0.05 else "%+.1f" % gap))
    s.append("</svg>")
    return "\n".join(s)


# ---------------------------------------------------------------- chart C ---
# The chart that is there now, against the denominator that belongs to it.
def chart_c():
    has = [r for r in ROWS if r["openCred"] >= 10]
    none = [r for r in ROWS if r["openCred"] < 10]
    has.sort(key=lambda r: -(r["ratioCred"] or 0))
    W, padL, plotW, padT, rowH = 1180, 300, 560, 56, 31
    H = padT + (len(has) + len(none) + 1) * rowH + 24
    mx = 70.0
    X = lambda v: padL + min(v, mx) / mx * plotW
    s = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="VSCS graduates as a '
         'share of the credential-requiring openings in each occupation group">' % (W, H)]
    for t in (0, 20, 40, 60):
        s.append('<line class="grid" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                 % (X(t), padT - 12, X(t), padT + len(has) * rowH - 8))
        s.append('<text class="tick" x="%.1f" y="%d" text-anchor="middle">%d%%</text>'
                 % (X(t), padT - 20, t))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">OPENINGS</text>'
             % (W - 100, padT - 20))
    s.append('<text class="colhead" x="%d" y="%d" text-anchor="end">GRADUATES</text>'
             % (W - 4, padT - 20))
    for i, r in enumerate(has):
        y = padT + i * rowH
        s.append('<text class="clab" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 16, y + 16, short(r["f"], 40)))
        s.append('<rect x="%d" y="%d" width="%.1f" height="21" rx="3" fill="var(%s)"/>'
                 % (padL, y + 1, max(2, X(r["ratioCred"]) - padL),
                    "--ord5" if r["linked"] else "--ord2"))
        s.append('<text class="vlab" x="%.1f" y="%d">%.0f%%</text>'
                 % (X(r["ratioCred"]) + 10, y + 16, r["ratioCred"]))
        s.append('<text class="fig" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (W - 100, y + 16, fmt(r["openCred"])))
        s.append('<text class="fig" x="%d" y="%d" text-anchor="end">%.1f</text>'
                 % (W - 4, y + 16, r["linked"]))
    y0 = padT + len(has) * rowH + 14
    s.append('<line class="lane" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (padL - 290, y0, W - 4, y0))
    s.append('<text class="figsub" x="%d" y="%d">No openings here ask for a credential '
             'VSCS awards, so there is nothing to measure against</text>' % (padL - 290, y0 + 18))
    for i, r in enumerate(none):
        y = y0 + 26 + i * rowH
        s.append('<text class="clab dim" x="%d" y="%d" text-anchor="end">%s</text>'
                 % (padL - 16, y + 16, short(r["f"], 40)))
        s.append('<text class="figsub" x="%d" y="%d">%s openings a year, none of them '
                 'asking for one</text>' % (padL, y + 16, fmt(r["openAll"])))
    s.append("</svg>")
    return "\n".join(s)


# -------------------------------------------------------------------- page ---
def srcblock(line, uses):
    rows = "".join("<tr><th>%s</th><td>%s</td></tr>" % (a, b) for a, b in uses)
    return ('<p class="src">%s</p>'
            '<details class="uses"><summary>What this chart uses</summary>'
            '<table>%s</table></details>' % (line, rows))


hp = [r for r in ROWS if r["f"].startswith("Healthcare Pract")][0]
bf = [r for r in ROWS if r["f"].startswith("Business")][0]
ed = [r for r in ROWS if r["f"].startswith("Educational")][0]
legal = [r for r in ROWS if r["f"] == "Legal"][0]
zero = [r for r in ROWS if not r["linked"]]
zero_cred = sum(r["openCred"] for r in zero)
zero_all = sum(r["openAll"] for r in zero)
ratio_all = TOT_LINK / sum(r["openAll"] for r in ROWS) * 100
ratio_cred = TOT_LINK / TOT_CRED * 100

CSS = r"""
:root{
  --s1:#009ba5; --ord1:#ccebed; --ord2:#99d7db; --ord3:#66c3c9; --ord4:#33afb7; --ord5:#009ba5;
  --ink:#16202a; --ink-2:#41505e; --ink-3:#74838f; --flag:#b4532f;
  --bg:#f7f8f8; --panel:#fff; --rule:#e4e8ea; --rule-2:#cfd6da; --track:#e8ecee; --cool:#e9f5f6;
  --display:'EB Garamond',Georgia,serif;
  --body:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --fig:'DM Mono',ui-monospace,'SF Mono',Menlo,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ink:#eef2f4; --ink-2:#b4c0c8; --ink-3:#8a97a1; --flag:#e8a088;
  --bg:#11171c; --panel:#19212a; --rule:#273139; --rule-2:#36434d; --track:#222c35; --cool:#14313a;
  --s1:#33afb7; --ord1:#0f3a3f; --ord2:#15606a; --ord3:#008c9b; --ord4:#33afb7; --ord5:#66c3c9;
  color-scheme:dark;
}}
:root[data-theme="dark"]{
  --ink:#eef2f4; --ink-2:#b4c0c8; --ink-3:#8a97a1; --flag:#e8a088;
  --bg:#11171c; --panel:#19212a; --rule:#273139; --rule-2:#36434d; --track:#222c35; --cool:#14313a;
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
.lane{stroke:var(--rule-2);stroke-width:1}
.tick{font-family:var(--fig);font-size:10px;fill:var(--ink-3)}
.colhead{font-family:var(--body);font-size:10px;letter-spacing:.09em;fill:var(--ink-3);font-weight:500}
.clab{font-family:var(--body);font-size:12.5px;fill:var(--ink)}
.clab.dim{fill:var(--ink-3)}
.vlab{font-family:var(--fig);font-size:12px;fill:var(--ink);font-weight:500}
.fig{font-family:var(--fig);font-size:11.5px;fill:var(--ink);font-weight:500}
.figsub{font-family:var(--fig);font-size:11px;fill:var(--ink-3)}
.flag{font-family:var(--fig);font-size:11px;fill:var(--flag);font-weight:500}
.brk{fill:none;stroke:var(--ink-2);stroke-width:1.2}
.brklab{font-family:var(--body);font-size:12.5px;fill:var(--ink);font-weight:500}
.conn{stroke:var(--rule-2);stroke-width:2.5}
.conn.up{stroke:var(--ord3)}
.conn.dn{stroke:var(--ord2)}
.dGrad{fill:var(--ord5)}
.dOpen{fill:var(--ink-3)}
.legend{display:flex;flex-wrap:wrap;gap:17px;margin:0 0 13px;font-size:12px;color:var(--ink-2)}
.legend span{display:flex;align-items:center;gap:6px}
.legend i{width:13px;height:13px;border-radius:3px;display:inline-block}
.legend i.dot{border-radius:50%}
table.fx{border-collapse:collapse;width:100%;min-width:560px;font-size:13px}
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
  h1{font-size:26px} h2{font-size:21px} .panel{padding:16px 14px 13px} .chart{min-width:760px}
}
"""

HTML = f"""<title>VSCS Alignment</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&family=EB+Garamond:wght@500;600&display=swap">
<style>{CSS}</style>

<div class="wrap">
  <h1>VSCS alignment</h1>
  <p class="sub">Three ways to draw the question this tab exists to answer: does what
  VSCS graduates students in line up with where Vermont is hiring? The arithmetic is
  already right. What is wrong is the denominator it is measured against, and that
  changes every figure on the tab.</p>
  <p class="meta">Every figure here is recomputed from the committed JSON by
  <code>scripts/_vscsfacts2.py</code>. No query was run.
  {fmt(V["totalCompletions"])} completions from {V["nCip"]} programs, 2024, against
  Vermont openings.</p>

  <div class="panel">
    <h3>The problem: VSCS is being measured against jobs it was never going to supply</h3>
    <p class="cap">The chart divides each occupation group&rsquo;s VSCS graduates by
    <em>all</em> of its annual openings. Most of those openings are in work that asks for
    no credential at all.</p>
    <div class="cwrap"><table class="fx">
      <tr><th>Occupation group</th><th class="num">Graduates</th>
          <th class="num">All openings</th><th class="num">Asking for a VSCS credential</th>
          <th class="num">Against all</th><th class="num">Against those</th></tr>
      {"".join(
        f'<tr><td>{r["f"]}</td><td class="num">{r["linked"]:.1f}</td>'
        f'<td class="num">{fmt(r["openAll"])}</td><td class="num">{fmt(r["openCred"])}</td>'
        f'<td class="num">{"—" if r["ratioAll"] is None else "%.1f%%" % r["ratioAll"]}</td>'
        f'<td class="num">{"—" if r["ratioCred"] is None else "%.0f%%" % r["ratioCred"]}</td></tr>'
        for r in [hp, ed, bf,
                  [x for x in ROWS if x["f"].startswith("Healthcare Supp")][0],
                  [x for x in ROWS if x["f"].startswith("Personal Care")][0]])}
    </table></div>
    <div class="note"><strong>The whole system reads {ratio_all:.1f}% against all openings and
    {ratio_cred:.1f}% against the ones that ask for a credential it awards.</strong> Only
    {V["openCred"] / V["openAll"] * 100:.0f}% of Vermont&rsquo;s {fmt(V["openAll"])} annual
    openings do. It matters most at the bottom of the chart: the five groups drawn with
    no graduates hold {fmt(zero_all)} openings a year between them and
    <strong>{fmt(zero_cred)}</strong> that ask for a VSCS credential. Four of them are
    work a college is not the route into. One is not &mdash; Legal has
    {fmt(legal["openCred"])} credential-requiring openings a year and no VSCS graduates at
    all &mdash; and the current chart buries that real gap among four false ones.</div>
    {srcblock(
      "Federal completions data, 2024, against Vermont openings · openings are Lightcast "
      "2021&ndash;2025 &divide; 4 · &ldquo;asking for a VSCS credential&rdquo; is an entry "
      "credential of sub-baccalaureate, bachelor&rsquo;s or graduate",
      [("Graduates attributed", "data/sow.json → vscs.byFamily[].linked"),
       ("Openings and entry credential", "data/lightcast.json → allOcc[].o, .t, .f"),
       ("The credential-requiring total", "data/sow.json → vscs.openCred (17,437), which the tab already carries and does not use"),
       ("Built by", "scripts/build_sow.py, scripts/build.py"),
       ("The allocation", "CIP-to-SOC is many-to-many, so each program&rsquo;s completions are split across its linked occupations in proportion to Vermont employment. A model of where graduates go, not an observation.")])}
  </div>

  <hr class="sep">

  <div class="opt">
    <span class="tag">Option A</span>
    <h2>The whole thing on one scale</h2>
    <p class="sub">Before any ranking: how big VSCS production is against the hiring it
    could serve. Four figures, one axis, because the proportion between them is the
    entire point and giving each its own axis destroys it.</p>
  </div>

  <div class="panel">
    <h3>How much of Vermont&rsquo;s hiring could VSCS supply?</h3>
    <p class="cap">All four bars are drawn on the same scale. The first is every opening
    in Vermont in a year; the second is the share of them whose entry credential is one
    VSCS awards; the third and fourth are what VSCS graduates and how much of that lands
    in a Vermont occupation at all.</p>
    <div class="cwrap">{chart_a()}</div>
    <div class="note">Read it as scale, not as a success rate: {ratio_cred:.1f}% is
    graduates against openings, never the share of openings filled. Vermont fills those
    jobs from everywhere &mdash; other colleges, people moving in, people already in work
    &mdash; and nothing on this dashboard can say in what proportion.</div>
    {srcblock(
      "Federal completions data, 2024, against Vermont openings · "
      + fmt(V["totalCompletions"]) + " completions from " + str(V["nCip"]) + " programs · "
      "openings are Lightcast 2021&ndash;2025 &divide; 4",
      [("Completions", "data/sow.json → vscs.totalCompletions (IPEDS 2024, CCV and Vermont State University)"),
       ("Linked to an occupation", "data/sow.json → vscs.byFamily[].linked, summed — " + fmt(TOT_LINK) + " of " + fmt(V["totalCompletions"]) + "; the rest feed occupations with no Vermont employment"),
       ("Openings", "data/lightcast.json → openTotal ÷ openYears"),
       ("Credential-requiring openings", "data/sow.json → vscs.openCred"),
       ("Built by", "scripts/build_sow.py")])}
  </div>

  <div class="opt">
    <span class="tag">Option B</span>
    <h2>Where production goes against where demand is</h2>
    <p class="sub">Two shares of two different totals, which is what makes them
    comparable. What share of VSCS&rsquo;s graduates go to each group, and what share of
    the credential-requiring openings each group has. Where the two dots sit apart, the
    shape of production and the shape of demand disagree.</p>
  </div>

  <div class="panel">
    <h3>Does the shape of VSCS production match the shape of demand?</h3>
    <p class="cap">One row per occupation group. The dark dot is that group&rsquo;s share
    of all VSCS graduates; the grey dot is its share of all credential-requiring openings.
    Both are shares of their own total, so they are on the same axis without either being
    a rate. Sorted by the gap. Click a row for the occupations inside it.</p>
    <div class="legend">
      <span><i class="dot" style="background:var(--ord5)"></i>Share of VSCS graduates</span>
      <span><i class="dot" style="background:var(--ink-3)"></i>Share of credential-requiring openings</span>
      <span><i style="background:var(--ord3)"></i>More graduates than demand&rsquo;s share</span>
      <span><i style="background:var(--ord2)"></i>Fewer</span>
    </div>
    <div class="cwrap">{chart_b()}</div>
    <div class="note">Two groups account for most of the disagreement.
    <strong>Healthcare Practitioners takes {hp["shareGrad"]:.0f}% of VSCS graduates against
    {hp["shareOpen"]:.0f}% of the openings</strong> &mdash; the single largest alignment
    in the system, and also the single largest concentration.
    <strong>Business &amp; Financial Operations is {bf["shareGrad"]:.0f}% of graduates
    against {bf["shareOpen"]:.0f}% of openings</strong>, and Educational Instruction
    {ed["shareGrad"]:.0f}% against {ed["shareOpen"]:.0f}%. None of that says the mix is
    wrong: a gap can be the right answer where another supplier serves the work.</div>
    {srcblock(
      "Federal completions data, 2024, against Vermont openings · shares of "
      + fmt(TOT_LINK) + " attributed graduates and " + fmt(TOT_CRED) + " credential-requiring "
      "openings a year · 22 occupation groups",
      [("Graduates by group", "data/sow.json → vscs.byFamily[].linked"),
       ("Credential-requiring openings by group", "data/lightcast.json → allOcc[].o summed over occupations whose .t is sub-baccalaureate, bachelor&rsquo;s or graduate"),
       ("Built by", "scripts/build_sow.py, scripts/build.py"),
       ("Why two shares rather than a ratio", "a ratio of graduates to openings invites reading it as the share of openings filled. Two shares of two totals cannot be read that way."),
       ("Caveat", "one year of completions against one year of openings, counting credentials rather than people — one person earning two counts twice.")])}
  </div>

  <div class="opt">
    <span class="tag">Option C</span>
    <h2>The ratio, against the right denominator</h2>
    <p class="sub">Closest to what is on the tab now: graduates as a percentage of
    openings, per group. Only the denominator changes, and the groups with nothing to
    measure against are set apart rather than drawn as zeros.</p>
  </div>

  <div class="panel">
    <h3>Where does VSCS production line up with the openings that ask for it?</h3>
    <p class="cap">Each occupation group&rsquo;s VSCS graduates measured against the
    openings it has each year <em>whose entry credential is one VSCS awards</em>. The
    groups below the line have no such openings, so there is no ratio to draw &mdash; they
    are not a gap, they are work a college is not the route into.</p>
    <div class="cwrap">{chart_c()}</div>
    <div class="note">The ordering changes as well as the level. Personal Care &amp;
    Service goes from near the foot of the chart to
    <strong>{[r for r in ROWS if r["f"].startswith("Personal Care")][0]["ratioCred"]:.0f}%</strong>,
    because almost none of its openings ask for a credential and VSCS graduates into the
    few that do. A high ratio on a small base is not the same finding as a high ratio on
    a large one, which is why the openings column sits beside it.</div>
    {srcblock(
      "Federal completions data, 2024, against Vermont openings asking for a "
      "sub-baccalaureate, bachelor&rsquo;s or graduate credential · "
      + fmt(TOT_CRED) + " openings a year",
      [("Graduates by group", "data/sow.json → vscs.byFamily[].linked"),
       ("Denominator", "data/lightcast.json → allOcc[].o over occupations whose .t is a credential VSCS awards"),
       ("Built by", "scripts/build_sow.py, scripts/build.py"),
       ("Not a fill rate", "graduates as a percentage of openings. Never the share of openings filled, which nothing here can tell you.")])}
  </div>

  <hr class="sep">

  <div class="rec">
    <h3>What I would build</h3>
    <ol>
      <li><strong>Fix the denominator first</strong>, whichever layout you pick. It is one
      line of arithmetic, <code>sow.json</code> already carries the total, and it changes
      the headline from {ratio_all:.1f}% to {ratio_cred:.1f}% and reorders the chart.</li>
      <li><strong>Option A opens the tab</strong>, as its own section or above
      <em>Production by award</em>. Nobody can read the rest of this tab correctly without
      first seeing that VSCS graduates {fmt(V["totalCompletions"])} people a year into a
      market with {fmt(V["openCred"])} openings it could serve, and that chart takes four
      bars.</li>
      <li><strong>Option B replaces the ratio chart</strong> under <em>Against demand</em>,
      with the occupation-level table kept where it is. Two shares cannot be misread as a
      fill rate, which the current chart has to warn against twice in its own caption and
      once in its how-to line.</li>
      <li><strong>Option C if you would rather change one thing.</strong> It keeps the
      chart the tab already has and only corrects what it is divided by. Less to explain,
      and it leaves the fill-rate misreading available.</li>
      <li><strong>Click-through on whichever ships</strong>, as the other tabs now carry
      it &mdash; a pane with the group&rsquo;s figures and the occupations inside it, then
      the full table.</li>
    </ol>
  </div>
</div>
"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="").write(HTML)
print("wrote", os.path.abspath(OUT), len(HTML), "bytes")
