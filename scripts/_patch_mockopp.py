"""Replaces Option C with a lane plot. Throwaway.

The scatter put VSCS graduates on a continuous vertical axis, and the measure will
not take one: sixteen of the forty-nine occupations are exactly zero, so they
stacked on the floor of the chart in a single line, and a square-root scale only
made the floor more crowded. Six labels over that line collided with each other
and with the band label.

Pipeline is really three states -- none, thin, established -- so it belongs on a
categorical axis. Three lanes, openings across, and the question the section
exists to ask reads straight off the top lane.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_mock_opp.py")
s = io.open(P, encoding="utf-8").read()

start = s.index("# ---------------------------------------------------------------- chart C ---")
end = s.index("# ---------------------------------------------------------------- chart D ---")

NEW = '''# ---------------------------------------------------------------- chart C ---
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
        s.append('<text class="figsub" x="%d" y="%.1f" text-anchor="end">'
                 '%d occupations &#183; %s openings</text>'
                 % (padL - 18, mid + 13, len(mine), fmt(sum(r["o"] for r in mine))))
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
    return "\\n".join(s)


'''
s = s[:start] + NEW + s[end:]

# The copy that described the old axes.
OLDCAP = """    <p class="cap">One point per occupation clearing the screen: annual openings across,
    VSCS graduates attributed to it up, point size is employment. The vertical scale is
    square-rooted because most of these are near zero and the difference between none and
    three is the one that matters. The shaded band is 100+ openings a year against two
    graduates or fewer.</p>
    <div class="legend">
      <span><i style="background:var(--ord5)"></i>Hiring, with almost no pipeline</span>
      <span><i style="background:var(--ink-3);opacity:.45"></i>Everything else that clears the screen</span>
    </div>"""
NEWCAP = """    <p class="cap">One point per occupation clearing the screen, placed by annual openings
    and sorted into three lanes by how much VSCS already produces for it. Point size is
    employment. Pipeline is three states rather than a number — sixteen of these
    occupations have exactly no graduates attributed — so it is a lane rather than an
    axis, and the shaded lane is the one the section exists to find.</p>
    <div class="legend">
      <span><i style="background:var(--ord5)"></i>No VSCS pipeline</span>
      <span><i style="background:var(--ink-3);opacity:.45"></i>Thin or established</span>
      <span><i style="background:var(--quad)"></i>The lane with nothing behind it</span>
    </div>"""
assert s.count(OLDCAP) == 1
s = s.replace(OLDCAP, NEWCAP)

OLDNOTE = """    <div class="note"><strong>{len(gaps)} occupations sit in that band, carrying
    {fmt(gapOpen)} openings a year between them</strong> —
    {", ".join(short(r["n"], 34) for r in gaps[:3])} among them. None of this says VSCS
    should start a program: the scope of this work stops short of that, and a thin
    pipeline can be the right answer. It says where to look.</div>"""
NEWNOTE = """    <div class="note"><strong>{nNone} of the {len(CAND)} occupations clearing the screen
    have no VSCS pipeline at all, and they carry {fmt(noneOpen)} openings a year between
    them</strong> — {", ".join(short(r["n"], 34) for r in noneTop[:3])} among them. Read
    across that lane and the point is how far right it reaches: this is not a tail of
    small occupations, it is some of the hardest hiring on the list. None of it says VSCS
    should start a program — the scope of this work stops short of that, and no pipeline
    can be the right answer — it says where to look.</div>"""
assert s.count(OLDNOTE) == 1
s = s.replace(OLDNOTE, NEWNOTE)

OLDSRC = '''      "Vermont occupation data, 2025, against federal completions data, 2024 · "
      + str(len(CAND)) + " occupations clearing the screen · square-root scale on graduates · "
      "benchmark " + money(LWA) + " a year (" + LW + ")",'''
NEWSRC = '''      "Vermont occupation data, 2025, against federal completions data, 2024 · "
      + str(len(CAND)) + " occupations clearing the screen · lanes are none, under 8% of the "
      "occupation&rsquo;s openings, and above it · benchmark " + money(LWA) + " a year (" + LW + ")",'''
assert s.count(OLDSRC) == 1
s = s.replace(OLDSRC, NEWSRC)

# the figures the new note needs
OLDFACTS = """gaps = sorted([r for r in CAND if r["o"] >= 100 and r["linked"] <= 2], key=lambda r: -r["o"])
gapOpen = sum(r["o"] for r in gaps)"""
NEWFACTS = """noneTop = sorted([r for r in CAND if r["pipeline"] == "No VSCS pipeline"],
                 key=lambda r: -r["o"])
noneOpen = sum(r["o"] for r in noneTop)"""
assert s.count(OLDFACTS) == 1
s = s.replace(OLDFACTS, NEWFACTS)

# a lane rule needs a class
s = s.replace(".quad{fill:var(--quad)}", ".quad{fill:var(--quad)}\n.lane{stroke:var(--rule);stroke-width:1}")

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("_mock_opp.py patched,", len(s), "bytes")
