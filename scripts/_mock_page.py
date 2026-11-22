"""Writes the Wage quality mockup page, with the real figures inlined.

Throwaway. The scratchpad path is past Windows' 260-character limit, so the
write goes through the \\\\?\\ extended-length prefix -- an ordinary open() on
that path fails with "No such file or directory", which is not what it means.
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "_mock_wage.json")
OUT = ("\\\\?\\C:\\Users\\sam.toriola\\AppData\\Local\\Temp\\claude\\"
       "C--Users-sam-toriola-AppData-Roaming-Claude-scratch-workspaces-"
       "30a8ecca-645b-47e0-b02e-fc476e330e37-0dfe5b0a-be69-42b4-8067-29907f9400db-"
       "scratch-2026-09-17-4ca2d0\\b5a173ea-8a3e-4a77-a615-dd7aeea4badd\\scratchpad\\"
       "wage-options.html")
# A second copy inside the repo, because the scratchpad path is past the limit
# the browser will open. _shots/ is gitignored.
LOCAL = os.path.join(HERE, "..", "_shots", "wage-options.html")

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wage Quality Options</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@500;600&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap">
<style>
  :root {
    --ocean: #009ba5; --ember: #fc4c3a; --vine: #4fcb00; --pine: #007a58;
    --ink: #16202a; --ink-2: #41505e; --ink-3: #74838f;
    --bg: #f7f8f8; --panel: #ffffff; --rule: #e4e8ea; --rule-2: #cfd6da;
    --track: #e8ecee; --warm: #fdeeec; --cool: #e3f3f4;
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
      --ember: #fd7061; --pine: #339579;
      color-scheme: dark;
    }
  }
  :root[data-theme="dark"] {
    --ink: #eef2f4; --ink-2: #b4c0c8; --ink-3: #8a97a1;
    --bg: #11171c; --panel: #19212a; --rule: #273139; --rule-2: #36434d;
    --track: #222c35; --warm: #3a1f1c; --cool: #13353a;
    --ember: #fd7061; --pine: #339579;
    color-scheme: dark;
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

  /* The grammar the Employment and Demand tabs already use, so these read as
     the same dashboard rather than as a new one. */
  .howto { display: flex; gap: 14px; align-items: baseline; margin: 0 0 16px;
           padding: 0 0 12px; border-bottom: 1px solid var(--rule); }
  .howto .hlab { flex: none; font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase;
                 font-weight: 700; color: var(--ocean); }
  .howto p { margin: 0; font-size: 13px; }
  @media (max-width: 720px) { .howto { display: block; } .howto .hlab { display: block; margin-bottom: 5px; } }

  .ctlbar { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 30px; margin: 0 0 14px; }
  .rankctl { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 10px; }
  .sclab { font-size: 10px; letter-spacing: 0.11em; text-transform: uppercase;
           color: var(--ink-3); font-weight: 700; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chips button { font: inherit; font-size: 12px; padding: 4px 11px; border-radius: 999px;
                  border: 1px solid var(--rule-2); background: var(--panel); color: var(--ink-2);
                  cursor: pointer; }
  .chips button[aria-pressed="true"] { background: var(--ocean); border-color: var(--ocean); color: #fff; }
  .chips button:focus-visible { outline: 2px solid var(--ocean); outline-offset: 1px; }

  .filterbar { display: flex; flex-wrap: wrap; gap: 8px 10px; align-items: center;
               font-size: 12px; color: var(--ink-3); border: 1px dashed var(--rule-2);
               border-radius: 8px; padding: 9px 12px; margin-bottom: 14px; }
  .filterbar .pill { border: 1px solid var(--rule-2); border-radius: 999px; padding: 2px 9px;
                     color: var(--ink-2); background: var(--panel); }
  .filterbar .on { background: var(--cool); border-color: var(--ocean); color: var(--ocean); }

  .disclose { font-size: 12.5px; color: var(--ocean); margin-top: 12px; font-weight: 500; }

  svg { display: block; width: 100%; height: auto; }
  .scroller { overflow-x: auto; }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 16px; list-style: none; padding: 0;
            margin: 0 0 12px; font-size: 12px; color: var(--ink-2); }
  .legend li { display: flex; align-items: center; gap: 6px; }
  .sw { width: 11px; height: 11px; border-radius: 2px; display: inline-block; }

  .tbl { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; min-width: 560px; }
  th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--rule); }
  th { font-size: 10.5px; letter-spacing: 0.07em; text-transform: uppercase;
       color: var(--ink-3); font-weight: 700; white-space: nowrap; }
  td.n, th.n { text-align: right; font-family: var(--fig); font-variant-numeric: tabular-nums;
               white-space: nowrap; }
  td.up { color: var(--ember); font-weight: 600; }

  .opt { border: 1px solid var(--rule); border-radius: 12px; padding: 22px; margin-top: 18px;
         background: var(--panel); }
  .opt > h2 { margin-bottom: 2px; }
  .badge { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: 0.06em;
           text-transform: uppercase; padding: 2px 9px; border-radius: 4px;
           background: var(--cool); color: var(--ocean); margin-bottom: 10px; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 760px) { .grid2 { grid-template-columns: 1fr; } }
  .pro { font-size: 13px; }
  .pro ul { margin: 6px 0 0; padding-left: 18px; color: var(--ink-2); }
  .pro li { margin-bottom: 4px; }
  .tally { font-family: var(--fig); font-size: 12px; color: var(--ink-3); margin-top: 14px;
           border-top: 1px solid var(--rule); padding-top: 10px; }
  .note { font-size: 12.5px; color: var(--ink-3); }
</style>
</head>
<body>
<div class="wrap">
  <p class="eyebrow">Strada Education Foundation &middot; Vermont State Colleges System</p>
  <h1>Two ways to rebuild Wage quality</h1>
  <p class="lede">
    Both are driven by the same change underneath: the tab stops asking whether an
    occupation&rsquo;s <em>median</em> clears the living wage, and starts asking how much of
    the <em>work</em> does. Both keep the filters, the measure controls and the click-through
    the Employment and Demand tabs use. Pick the chart.
  </p>

  <section>
    <h2>The finding that makes the rebuild worth doing</h2>
    <p>
      Today a job counts as clearing the living wage if the median of its occupation does. An
      occupation whose median lands a dollar over contributes <strong>all</strong> its jobs to
      &ldquo;above&rdquo;; a dollar under and it contributes none. Half the people in each are
      on the wrong side of that line.
    </p>
    <p>
      Statewide the errors mostly cancel, which is why it has survived &mdash;
      <span class="num">42.5%</span> on the old rule against <span class="num">41.1%</span> read
      off the distributions. By occupation group they do not cancel, and the chart is what people
      read:
    </p>
    <div class="panel">
      <div class="tbl">
        <table>
          <thead>
            <tr><th>Occupation group</th><th class="n">Chart says below</th><th class="n">Actually below</th><th class="n">Out by</th></tr>
          </thead>
          <tbody id="corr"></tbody>
        </table>
      </div>
      <div class="readout" id="headline"></div>
      <div class="srcline">
        Vermont occupation data, 2025 &middot; each occupation&rsquo;s own p10&ndash;p90 ladder,
        weighted by its jobs &middot; benchmark: one adult, no children
      </div>
    </div>
  </section>

  <!-- ===================== OPTION A ===================== -->
  <div class="opt">
    <p class="badge">Option A</p>
    <h2>How much of the work falls short</h2>
    <p>
      One bar per row, filled from the left to the share of its jobs paying below the floor.
      Every row is on the same 0&ndash;100% track, so the ranking is the message and twenty-two
      rows stay readable.
    </p>

    <div class="howto">
      <span class="hlab">How to read this</span>
      <p>
        The filled part of each bar is the share of that work paying below the benchmark. Pick
        what the rows are and what the bar measures; the line underneath answers the pair.
        Click any bar for the occupations inside it.
      </p>
    </div>

    <div class="filterbar">
      <span>Filters</span>
      <span class="pill">Credential</span>
      <span class="pill">Occupation group</span>
      <span class="pill">Pay vs benchmark</span>
      <span class="pill">Size</span>
      <span class="pill on">1 adult, no children &times;</span>
      <span class="note">&mdash; the same bar Employment and Opportunities carry</span>
    </div>

    <div class="ctlbar">
      <div class="rankctl">
        <span class="sclab">Rows</span>
        <div class="chips" id="a-pool"></div>
      </div>
      <div class="rankctl">
        <span class="sclab">Measure</span>
        <div class="chips" id="a-meas"></div>
      </div>
    </div>

    <div class="panel">
      <h3 id="a-title"></h3>
      <p class="cap" id="a-cap"></p>
      <ul class="legend">
        <li><span class="sw" style="background:var(--ember)"></span>Below the benchmark</li>
        <li id="a-leg2"><span class="sw" style="background:var(--track)"></span>At or above it</li>
      </ul>
      <div class="scroller"><svg id="a-chart" role="img" aria-label="Share of jobs below the living wage"></svg></div>
      <div class="readout" id="a-note"></div>
      <p class="disclose">&rsaquo; Show the figures (22 occupation groups)</p>
      <div class="srcline" id="a-src"></div>
    </div>

    <div class="grid2" style="margin-top:16px">
      <div class="pro">
        <h3>What it is good at</h3>
        <ul>
          <li>One number per row, so the ranking is unambiguous</li>
          <li>Switching to <strong>People below</strong> reorders it completely &mdash; Food
              Preparation has the most people short, Healthcare Support the highest share</li>
          <li>Same horizontal-bar grammar as every other ranked chart here</li>
        </ul>
      </div>
      <div class="pro">
        <h3>What it hides</h3>
        <ul>
          <li>The spread. Two families at 30% can have completely different shapes</li>
          <li>How far below the floor the short jobs sit</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ===================== OPTION B ===================== -->
  <div class="opt">
    <p class="badge">Option B</p>
    <h2>The whole range, cut at the floor</h2>
    <p>
      One row per occupation group showing what it actually pays from the 10th to the 90th
      percentile, with the benchmark drawn through the chart. The part of the range left of the
      line is the part that falls short, in red. You read adequacy, typical pay and spread off
      one mark.
    </p>

    <div class="howto">
      <span class="hlab">How to read this</span>
      <p>
        The bar is the middle half of the pay in that work; the thin line runs from the lowest
        tenth to the highest. The dot is the midpoint job. The dashed line is the benchmark
        &mdash; move it with the household selector and every row shifts against it.
      </p>
    </div>

    <div class="filterbar">
      <span>Filters</span>
      <span class="pill">Credential</span>
      <span class="pill">Occupation group</span>
      <span class="pill">Pay vs benchmark</span>
      <span class="pill">Size</span>
      <span class="pill on">1 adult, no children &times;</span>
    </div>

    <div class="ctlbar">
      <div class="rankctl">
        <span class="sclab">Rows</span>
        <div class="chips" id="b-pool"></div>
      </div>
      <div class="rankctl">
        <span class="sclab">Order by</span>
        <div class="chips" id="b-sort"></div>
      </div>
    </div>

    <div class="panel">
      <h3 id="b-title"></h3>
      <p class="cap" id="b-cap"></p>
      <ul class="legend">
        <li><span class="sw" style="background:var(--ember)"></span>Pay below the benchmark</li>
        <li><span class="sw" style="background:var(--ocean)"></span>Pay above it</li>
        <li><span class="sw" style="background:var(--ink);border-radius:50%"></span>Midpoint job</li>
      </ul>
      <div class="scroller"><svg id="b-chart" role="img" aria-label="Pay range by occupation group against the living wage"></svg></div>
      <div class="readout" id="b-note"></div>
      <p class="disclose">&rsaquo; Show the figures (22 occupation groups)</p>
      <div class="srcline" id="b-src"></div>
    </div>

    <div class="grid2" style="margin-top:16px">
      <div class="pro">
        <h3>What it is good at</h3>
        <ul>
          <li>Shows <em>why</em> a family falls short &mdash; a low midpoint, or a long tail</li>
          <li>Healthcare Practitioners clears the floor at the midpoint and still runs
              <span class="num">$49,792</span> at the bottom tenth; the bar says so and a share cannot</li>
          <li>The benchmark is a line you can see every row move against</li>
        </ul>
      </div>
      <div class="pro">
        <h3>What it costs</h3>
        <ul>
          <li>Five marks per row instead of one &mdash; it reads slower</li>
          <li>Ranking is ambiguous: order by midpoint, by bottom tenth or by share below</li>
          <li>Needs a wide chart; it is the weakest of the two on a phone</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ===================== SHARED ===================== -->
  <section>
    <h2>Either way, the second section is new</h2>
    <p>
      The cost floor is not the same everywhere, and the dashboard has been measuring every
      county against one statewide figure. Measuring each county against its own floor
      reorders the map &mdash; and the county slice now makes it possible.
    </p>

    <div class="howto">
      <span class="hlab">How to read this</span>
      <p>
        The share of each county&rsquo;s jobs paying below a living wage. Switch the benchmark
        between the county&rsquo;s own cost floor and one statewide figure, and watch which
        counties move.
      </p>
    </div>

    <div class="ctlbar">
      <div class="rankctl">
        <span class="sclab">Benchmark</span>
        <div class="chips" id="c-mode"></div>
      </div>
    </div>

    <div class="panel">
      <h3 id="c-title"></h3>
      <p class="cap" id="c-cap"></p>
      <div class="scroller"><svg id="c-chart" role="img" aria-label="Share of county jobs below a living wage"></svg></div>
      <div class="readout" id="c-note"></div>
      <div class="srcline">
        Vermont occupation data by county, 2025 &middot; employees &middot; each occupation&rsquo;s
        own pay ladder weighted by county employment &middot; county living wage, one adult, no
        children
      </div>
    </div>
  </section>

  <section>
    <h2>What the tab looks like after</h2>
    <div class="grid2">
      <div class="panel">
        <h3>Now</h3>
        <p class="note">Size and pay &mdash; typical pay by size band, share above the living
          wage by size band, every occupation as a scatter.<br>
          Largest occupations &mdash; share of jobs, pay spread.</p>
        <p class="note">
          Three of those five charts are organised by <strong>occupation size</strong>, which is
          a property of the classification rather than a question anyone brings. Nobody asks
          whether big occupations pay well; they ask whether <em>this</em> work pays enough.
        </p>
      </div>
      <div class="panel">
        <h3>After</h3>
        <p class="note">Does the work pay enough? &mdash; occupation groups, entry credential or the
          25 largest occupations, measured by share below or people below.<br>
          Where the floor bites &mdash; the 14 counties against their own cost floor.</p>
        <p class="note">
          Same two sections, one argument. The size bands go; the scatter survives as a third
          row option, where the benchmark line it already draws finally means something. And
          &ldquo;Largest occupations &rarr; share of jobs&rdquo; is an employment question &mdash;
          it would sit better on Employment.
        </p>
      </div>
    </div>
    <p class="tally">
      Charts: 5 &rarr; 4. Questions answered: 2 &rarr; 4, and one of them is new to the dashboard.
    </p>
  </section>
</div>

<script>window.__W__ = __DATA__;</script>
<script>
(function () {
  var D = window.__W__;
  var ns = 'http://www.w3.org/2000/svg';
  var FAM_SHORT = {
    'Office & Administrative Support': 'Office & Admin Support',
    'Educational Instruction & Library': 'Education & Library',
    'Healthcare Practitioners & Technical': 'Healthcare Practitioners',
    'Arts, Design, Entertainment & Media': 'Arts, Design & Media',
    'Installation, Maintenance & Repair': 'Installation & Repair',
    'Transportation & Material Moving': 'Transportation & Moving',
    'Business & Financial Operations': 'Business & Financial',
    'Life, Physical & Social Science': 'Life & Physical Science',
    'Food Preparation & Serving': 'Food Preparation',
    'Building & Grounds Cleaning': 'Building & Grounds',
    'Farming, Fishing & Forestry': 'Farming & Forestry',
    'Construction & Extraction': 'Construction',
    'Personal Care & Service': 'Personal Care'
  };
  function short(s) { return FAM_SHORT[s] || s; }
  function el(n, a, t) {
    var e = document.createElementNS(ns, n);
    for (var k in a) if (a[k] !== null && a[k] !== undefined) e.setAttribute(k, a[k]);
    if (t !== undefined) e.textContent = t;
    return e;
  }
  function num(v) { return Math.round(v).toLocaleString('en-US'); }
  function money(v) { return '$' + num(v); }
  function clear(s) { while (s.firstChild) s.removeChild(s.firstChild); }

  function chips(host, opts, initial, onPick) {
    var cur = initial;
    opts.forEach(function (o) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = o.label;
      b.setAttribute('aria-pressed', String(o.id === cur));
      b.addEventListener('click', function () {
        cur = o.id;
        Array.prototype.forEach.call(host.children, function (c) {
          c.setAttribute('aria-pressed', String(c === b));
        });
        onPick(o.id);
      });
      host.appendChild(b);
    });
    onPick(cur);
  }

  /* ---------- the correction table + headline ---------- */
  (function () {
    var rows = D.families.slice()
      .sort(function (a, b) { return Math.abs(b.below - b.oldBelow) - Math.abs(a.below - a.oldBelow); })
      .slice(0, 5);
    var tb = document.getElementById('corr');
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      var d = r.below - r.oldBelow;
      tr.innerHTML = '<td>' + short(r.f) + '</td>' +
        '<td class="n">' + r.oldBelow.toFixed(1) + '%</td>' +
        '<td class="n">' + r.below.toFixed(1) + '%</td>' +
        '<td class="n up">' + (d > 0 ? '+' : '') + d.toFixed(1) + '</td>';
      tb.appendChild(tr);
    });
    document.getElementById('headline').innerHTML =
      '<strong>' + num(D.belowJobs) + ' Vermont jobs &mdash; ' + D.belowShare +
      '% of all priced work &mdash; pay less than one adult needs to live here.</strong> ' +
      'That figure is the point of the tab, and it is not on it today.';
  })();

  /* ---------- Option A: share / count below the floor ---------- */
  (function () {
    var POOLS = { fam: D.families, cred: D.creds };
    var pool = 'fam', meas = 'share';

    function draw() {
      var rows = POOLS[pool].slice().sort(function (a, b) {
        return meas === 'share' ? b.below - a.below : b.belowN - a.belowN;
      });
      var W = 1040, labW = 212, padR = 92, padT = 30, rowH = 22, gap = 7;
      var H = padT + rows.length * (rowH + gap) + 6;
      var plotW = W - labW - padR;
      // A count axis wants round ticks, not quarters of whatever the longest
      // bar happens to be -- 5,183 and 10,366 are not numbers anyone reads.
      function nice(v) {
        var mag = Math.pow(10, Math.floor(Math.log10(v)));
        var steps = [1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10];
        for (var i = 0; i < steps.length; i++) if (steps[i] * mag >= v) return steps[i] * mag;
        return 10 * mag;
      }
      var max = meas === 'share' ? 100
        : nice(Math.max.apply(null, rows.map(function (r) { return r.belowN; })) / 4) * 4;
      document.getElementById('a-leg2').style.display = meas === 'share' ? '' : 'none';
      var svg = document.getElementById('a-chart');
      svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
      clear(svg);

      var ticks = meas === 'share' ? [0, 25, 50, 75, 100] : [0, max / 4, max / 2, 3 * max / 4, max];
      ticks.forEach(function (t) {
        var x = labW + (t / max) * plotW;
        svg.appendChild(el('line', { x1: x, y1: padT - 8, x2: x, y2: H - 4,
          stroke: 'var(--rule)', 'stroke-width': 1 }));
        svg.appendChild(el('text', { x: x, y: padT - 14, 'text-anchor': 'middle',
          'font-size': 10, fill: 'var(--ink-3)', 'font-family': 'var(--fig)' },
          meas === 'share' ? t + '%' : num(t)));
      });

      rows.forEach(function (r, i) {
        var y = padT + i * (rowH + gap);
        var v = meas === 'share' ? r.below : r.belowN;
        var w = (v / max) * plotW;
        if (meas === 'share') {
          svg.appendChild(el('rect', { x: labW, y: y, width: plotW, height: rowH, rx: 3,
            fill: 'var(--track)' }));
        }
        svg.appendChild(el('rect', { x: labW, y: y, width: Math.max(1.5, w), height: rowH,
          rx: 3, fill: 'var(--ember)' }));
        svg.appendChild(el('text', { x: labW - 11, y: y + rowH / 2 + 4, 'text-anchor': 'end',
          'font-size': 12, fill: 'var(--ink)' }, short(r.f)));
        svg.appendChild(el('text', { x: labW + plotW + 9, y: y + rowH / 2 + 4,
          'font-size': 11.5, fill: 'var(--ink-2)', 'font-family': 'var(--fig)' },
          meas === 'share' ? r.below.toFixed(1) + '%' : num(r.belowN)));
      });

      var top = rows[0];
      var alt = POOLS[pool].slice().sort(function (a, b) {
        return meas === 'share' ? b.belowN - a.belowN : b.below - a.below;
      })[0];
      document.getElementById('a-title').textContent = meas === 'share'
        ? 'How much of each occupation group pays below a living wage?'
        : 'How many people are in work that pays below a living wage?';
      document.getElementById('a-cap').textContent = meas === 'share'
        ? 'The share of each row\u2019s jobs paying under the benchmark, read off every occupation\u2019s own pay distribution rather than from its median.'
        : 'The same calculation weighted by employment, so a large row with a moderate share outranks a small row with a high one.';
      document.getElementById('a-note').innerHTML = meas === 'share'
        ? '<strong>' + short(top.f) + '</strong> is the work least likely to pay a living wage: ' +
          top.below.toFixed(0) + '% of its ' + num(top.jobs) + ' jobs fall short. But the most ' +
          'people short are in <strong>' + short(alt.f) + '</strong> \u2014 ' + num(alt.belowN) +
          ' of them. Switch the measure.'
        : '<strong>' + short(top.f) + '</strong> holds the most people paid under the benchmark \u2014 ' +
          num(top.belowN) + ' \u2014 though only ' + top.below.toFixed(0) + '% of it falls short. ' +
          'By share the answer is <strong>' + short(alt.f) + '</strong> at ' + alt.below.toFixed(0) + '%.';
      document.getElementById('a-src').textContent =
        'Vermont occupation data, 2025 \u00b7 ' + num(D.totalJobs) + ' priced jobs \u00b7 benchmark ' +
        money(D.lwA) + ' a year (' + D.lwKey + ') \u00b7 share read off each occupation\u2019s p10\u2013p90 ladder';
    }

    chips(document.getElementById('a-pool'), [
      { id: 'fam', label: '22 occupation groups' },
      { id: 'cred', label: 'Entry credential' }
    ], 'fam', function (v) { pool = v; draw(); });
    chips(document.getElementById('a-meas'), [
      { id: 'share', label: 'Share of jobs below' },
      { id: 'count', label: 'People below' }
    ], 'share', function (v) { meas = v; draw(); });
  })();

  /* ---------- Option B: the pay ladder, cut at the floor ---------- */
  (function () {
    var POOLS = { fam: D.families, cred: D.creds };
    var pool = 'fam', sort = 'med';
    var AXMAX = 200000;

    function draw() {
      var rows = POOLS[pool].slice().sort(function (a, b) {
        if (sort === 'med') return a.box.p50 - b.box.p50;
        if (sort === 'low') return a.box.p10 - b.box.p10;
        return b.below - a.below;
      });
      var W = 1040, labW = 212, padR = 86, padT = 42, rowH = 24, gap = 8;
      var H = padT + rows.length * (rowH + gap) + 10;
      var plotW = W - labW - padR;
      var x = function (v) { return labW + Math.min(v, AXMAX) / AXMAX * plotW; };
      var svg = document.getElementById('b-chart');
      svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
      clear(svg);

      [0, 50000, 100000, 150000, 200000].forEach(function (t) {
        svg.appendChild(el('line', { x1: x(t), y1: padT - 8, x2: x(t), y2: H - 8,
          stroke: 'var(--rule)', 'stroke-width': 1 }));
        svg.appendChild(el('text', { x: x(t), y: padT - 14, 'text-anchor': 'middle',
          'font-size': 10, fill: 'var(--ink-3)', 'font-family': 'var(--fig)' },
          t ? '$' + (t / 1000) + 'k' : '$0'));
      });

      var fx = x(D.lwA);
      svg.appendChild(el('line', { x1: fx, y1: padT - 10, x2: fx, y2: H - 8,
        stroke: 'var(--ink-2)', 'stroke-width': 1.5, 'stroke-dasharray': '4 3' }));
      svg.appendChild(el('text', { x: fx + 5, y: H - 1, 'font-size': 9.5,
        fill: 'var(--ink-2)', 'font-family': 'var(--fig)' }, 'Living wage ' + money(D.lwA)));

      rows.forEach(function (r, i) {
        var y = padT + i * (rowH + gap), cy = y + rowH / 2;
        var b = r.box;
        var lowCol = 'var(--ember)', hiCol = 'var(--ocean)', cut = D.lwA;
        function seg(v0, v1, h, col) {
          if (v1 <= v0) return;
          svg.appendChild(el('rect', { x: x(v0), y: cy - h / 2, width: Math.max(1, x(v1) - x(v0)),
            height: h, rx: h > 6 ? 3 : 1, fill: col }));
        }
        // Each span is cut at the benchmark wherever it crosses it, so the red
        // is exactly the part of the range that falls short -- a whisker that
        // starts below the line and ends above it is two colours, not one.
        function span(v0, v1, h) {
          if (v1 <= cut) seg(v0, v1, h, lowCol);
          else if (v0 >= cut) seg(v0, v1, h, hiCol);
          else { seg(v0, cut, h, lowCol); seg(cut, v1, h, hiCol); }
        }
        span(b.p10, b.p25, 3);
        span(b.p25, b.p75, 14);
        span(b.p75, b.p90, 3);
        svg.appendChild(el('circle', { cx: x(b.p50), cy: cy, r: 4.2, fill: 'var(--ink)',
          stroke: 'var(--panel)', 'stroke-width': 1.5 }));
        if (b.p90 > AXMAX) {
          svg.appendChild(el('text', { x: labW + plotW + 2, y: cy + 4, 'font-size': 11,
            fill: 'var(--ink-3)' }, '\u203a'));
        }
        svg.appendChild(el('text', { x: labW - 11, y: cy + 4, 'text-anchor': 'end',
          'font-size': 12, fill: 'var(--ink)' }, short(r.f)));
        svg.appendChild(el('text', { x: labW + plotW + 13, y: cy + 4, 'font-size': 11,
          fill: 'var(--ink-2)', 'font-family': 'var(--fig)' }, r.below.toFixed(0) + '%'));
      });

      // Above the tick row rather than on it: the $200k tick sits in the same place.
      svg.appendChild(el('text', { x: labW + plotW + 13, y: padT - 26, 'font-size': 9.5,
        fill: 'var(--ink-3)' }, 'share below'));

      var worst = POOLS[pool].slice().sort(function (a, b) { return b.below - a.below; })[0];
      var widest = POOLS[pool].slice().sort(function (a, b) {
        return (b.box.p90 / b.box.p10) - (a.box.p90 / a.box.p10);
      })[0];
      document.getElementById('b-title').textContent = 'What does each occupation group actually pay?';
      document.getElementById('b-cap').textContent =
        'The bar is the middle half of the pay in that work, the thin line the tenth to the ninetieth percentile, the dot the midpoint job. Red is the part of the range below the benchmark. Percentages on the right are the share of jobs below it.';
      document.getElementById('b-note').innerHTML =
        '<strong>' + short(worst.f) + '</strong> sits almost entirely left of the line \u2014 ' +
        worst.below.toFixed(0) + '% of its jobs pay under ' + money(D.lwA) + ', and even its top ' +
        'tenth reaches only ' + money(worst.box.p90) + '. The widest range is <strong>' +
        short(widest.f) + '</strong>: ' + money(widest.box.p10) + ' to ' + money(widest.box.p90) +
        ', or ' + (widest.box.p90 / widest.box.p10).toFixed(1) + ' times, which is the thing a ' +
        'single share cannot tell you.';
      document.getElementById('b-src').textContent =
        'Vermont occupation data, 2025 \u00b7 percentiles pooled from the occupations inside each row and weighted by employment \u00b7 axis clipped at $200k, \u203a marks a range running past it';
    }

    chips(document.getElementById('b-pool'), [
      { id: 'fam', label: '22 occupation groups' },
      { id: 'cred', label: 'Entry credential' }
    ], 'fam', function (v) { pool = v; draw(); });
    chips(document.getElementById('b-sort'), [
      { id: 'med', label: 'Midpoint pay' },
      { id: 'low', label: 'Bottom tenth' },
      { id: 'below', label: 'Share below' }
    ], 'med', function (v) { sort = v; draw(); });
  })();

  /* ---------- shared: counties against their own floor ---------- */
  (function () {
    var mode = 'local';

    function draw() {
      var key = mode === 'local' ? 'local' : 'state';
      var rows = D.counties.slice().sort(function (a, b) { return b[key] - a[key]; });
      var W = 1040, labW = 150, padR = 150, padT = 30, rowH = 22, gap = 7;
      var H = padT + rows.length * (rowH + gap) + 6;
      var plotW = W - labW - padR;
      var svg = document.getElementById('c-chart');
      svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
      clear(svg);

      [0, 15, 30, 45, 60].forEach(function (t) {
        var x = labW + t / 60 * plotW;
        svg.appendChild(el('line', { x1: x, y1: padT - 8, x2: x, y2: H - 4,
          stroke: 'var(--rule)', 'stroke-width': 1 }));
        svg.appendChild(el('text', { x: x, y: padT - 14, 'text-anchor': 'middle',
          'font-size': 10, fill: 'var(--ink-3)', 'font-family': 'var(--fig)' }, t + '%'));
      });

      rows.forEach(function (r, i) {
        var y = padT + i * (rowH + gap);
        var w = r[key] / 60 * plotW;
        svg.appendChild(el('rect', { x: labW, y: y, width: Math.max(1.5, w), height: rowH,
          rx: 3, fill: 'var(--ember)', 'fill-opacity': r.thin ? 0.45 : 1 }));
        svg.appendChild(el('text', { x: labW - 11, y: y + rowH / 2 + 4, 'text-anchor': 'end',
          'font-size': 12, fill: 'var(--ink)' }, r.c));
        svg.appendChild(el('text', { x: labW + w + 9, y: y + rowH / 2 + 4, 'font-size': 11.5,
          fill: 'var(--ink-2)', 'font-family': 'var(--fig)' }, r[key].toFixed(1) + '%'));
        if (mode === 'local') {
          svg.appendChild(el('text', { x: W - 6, y: y + rowH / 2 + 4, 'text-anchor': 'end',
            'font-size': 10.5, fill: 'var(--ink-3)', 'font-family': 'var(--fig)' },
            'floor ' + money(r.lwA)));
        }
      });

      var ch = D.counties.filter(function (r) { return r.c === 'Chittenden'; })[0];
      var or = D.counties.filter(function (r) { return r.c === 'Orleans'; })[0];
      var gi = D.counties.filter(function (r) { return r.c === 'Grand Isle'; })[0];
      document.getElementById('c-title').textContent = mode === 'local'
        ? 'How much of each county\u2019s work pays below that county\u2019s cost floor?'
        : 'How much of each county\u2019s work pays below one statewide floor?';
      var thinNames = D.counties.filter(function (r) { return r.thin; })
        .map(function (r) { return r.c; }).join(' and ');
      var thinNote = thinNames
        ? ' The two pale bars are ' + thinNames + ', which hold too few jobs to carry a figure this precise.'
        : '';
      document.getElementById('c-cap').textContent = (mode === 'local'
        ? 'Each county measured against its own living wage, which runs from ' +
          money(Math.min.apply(null, D.counties.map(function (r) { return r.lwA; }))) + ' to ' +
          money(Math.max.apply(null, D.counties.map(function (r) { return r.lwA; }))) + ' a year.'
        : 'Every county measured against the same statewide benchmark of ' + money(D.lwA) +
          ' \u2014 what the dashboard does today.') + thinNote;
      document.getElementById('c-note').innerHTML = mode === 'local'
        ? 'Against its own cost floor, <strong>Chittenden</strong> looks worse, not better: ' +
          ch.local.toFixed(0) + '% of its jobs fall short where the statewide benchmark said ' +
          ch.state.toFixed(0) + '%. <strong>Orleans</strong> moves the other way, ' +
          or.state.toFixed(0) + '% to ' + or.local.toFixed(0) + '%. The hardest place to clear ' +
          'the floor is <strong>Grand Isle</strong> at ' + gi.local.toFixed(0) + '%, which has ' +
          'the highest living wage in the state and the second-smallest labour market.'
        : 'On one statewide floor the poorest-paying counties look worst, which is the ' +
          'expected answer. Switch to the local floor and it changes: the high-cost counties ' +
          'move up and the low-cost ones move down.';
    }

    chips(document.getElementById('c-mode'), [
      { id: 'local', label: 'Each county\u2019s own floor' },
      { id: 'state', label: 'One statewide floor' }
    ], 'local', function (v) { mode = v; draw(); });
  })();
})();
</script>
</body>
</html>
"""

data = open(DATA, encoding="utf-8").read()
html = PAGE.replace("__DATA__", data)
os.makedirs(os.path.dirname(LOCAL), exist_ok=True)
for path in (OUT, LOCAL):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)
print("wrote %s bytes" % f"{len(html):,}")
print("  preview: %s" % os.path.abspath(LOCAL))
