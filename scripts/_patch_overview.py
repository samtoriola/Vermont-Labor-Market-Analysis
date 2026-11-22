"""Review 11/18, Overview: a credential filter, a sort, and a visible light end.

THE COLOUR. The ramp's first step is Ocean at 20% -- #ccebed -- which on a white
panel is about 1.2:1 against the surface. Management at 3% below the benchmark
drew as a bar you have to look for, which is the opposite of what a bar is for.
The ramp now runs over the top four fifths of the same Ocean tint scale (40, 55,
70, 85, 100%) instead of the whole of it, so the lightest band is a colour rather
than a suggestion. Adjacent steps are closer together as a result; every bar
already prints its own percentage in the BELOW column, which is the secondary
encoding that makes that legal. Dark mode gets the same treatment at its own end.

Kept separate from --ord1..5 rather than changing those, because the concentration
grid and the age mix use the full scale and neither has this problem: they are
grids of small cells, not long bars against a page.

THE CREDENTIAL FILTER narrows the occupations BEFORE the roll-up, so a group's
shading becomes the share of its jobs AT THAT TIER paying below the benchmark --
not its overall share redrawn shorter. The caption says which it is.

THE SORT is on the chart. The table underneath could always sort by any column;
the chart could only ever rank by size, which is the one measure that is not the
finding.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------- globals.css ---
CSS = os.path.join(H, "..", "app", "globals.css")
css = io.open(CSS, encoding="utf-8").read()
css_subs = [
    ("""  --ord1: #ccebed;
  --ord2: #99d7db;
  --ord3: #66c3c9;
  --ord4: #33afb7;
  --ord5: #009ba5;""",
     """  --ord1: #ccebed;
  --ord2: #99d7db;
  --ord3: #66c3c9;
  --ord4: #33afb7;
  --ord5: #009ba5;

  /* The Overview's ramp: the same Ocean tints, but starting at 40% rather than
     20%. A full-width bar at --ord1 is barely a bar on a white panel. */
  --ovr1: #99d7db;
  --ovr2: #73c9cf;
  --ovr3: #4dbcc3;
  --ovr4: #26aeb7;
  --ovr5: #009ba5;""", 1),
]
# Both dark-mode blocks carry the inverted ramp; both get the Overview's.
css_subs.append((
    """    --ord1: #0f3a3f;
    --ord2: #15606a;
    --ord3: #008c9b;
    --ord4: #33afb7;
    --ord5: #66c3c9;""",
    """    --ord1: #0f3a3f;
    --ord2: #15606a;
    --ord3: #008c9b;
    --ord4: #33afb7;
    --ord5: #66c3c9;

    --ovr1: #15606a;
    --ovr2: #0d7d8a;
    --ovr3: #008c9b;
    --ovr4: #33afb7;
    --ovr5: #66c3c9;""", 1))
css_subs.append((
    """  --ord1: #0f3a3f;
  --ord2: #15606a;
  --ord3: #008c9b;
  --ord4: #33afb7;
  --ord5: #66c3c9;""",
    """  --ord1: #0f3a3f;
  --ord2: #15606a;
  --ord3: #008c9b;
  --ord4: #33afb7;
  --ord5: #66c3c9;

  --ovr1: #15606a;
  --ovr2: #0d7d8a;
  --ovr3: #008c9b;
  --ovr4: #33afb7;
  --ovr5: #66c3c9;""", 1))

for old, _, want in css_subs:
    if css.count(old) != want:
        raise SystemExit("globals.css: %d of %r, expected %d" % (css.count(old), old[:50], want))

# ------------------------------------------------------------- Overview.js ---
P = os.path.join(H, "..", "components", "views", "Overview.js")
s = io.open(P, encoding="utf-8").read()

subs = [
    ("import { LC, PCT, TOTJ, lwAnnual, occByFamily } from '@/lib/data';",
     "import { LC, PCT, TIER_ORDER, TOTJ, lwAnnual, occByFamily } from '@/lib/data';"),

    ("import { Panel, Legend, Tiles, LwPicker } from '../ui';",
     "import { Panel, Legend, PickerPair, Tiles, LwPicker } from '../ui';"),

    (""" * THE RAMP
 * --ord1 to --ord5, the house sequential scale the concentration grid and the
 * age mix already use. Not a red one: red reads as a warning that the reader is
 * meant to act on, and this is a measurement. The ramp inverts between light and
 * dark so that ord1 is always the least and ord5 the most.""",
     """ * THE RAMP
 * --ovr1 to --ovr5: the house Ocean tints, but over the top four fifths of the
 * scale rather than all of it. The grid and the age mix use the full --ord1..5
 * and are right to -- they are small cells. A bar is long and sits against the
 * page, and --ord1 at 20% tint was a bar you had to hunt for, which is what the
 * review caught. Not a red ramp: red reads as a warning the reader is meant to
 * act on, and this is a measurement. The ramp inverts between light and dark so
 * the first step is always the least and the fifth the most."""),

    ("""const BANDS = [
  { max: 10, color: '--ord1', label: 'Under 10%' },
  { max: 30, color: '--ord2', label: '10 to 30%' },
  { max: 50, color: '--ord3', label: '30 to 50%' },
  { max: 75, color: '--ord4', label: '50 to 75%' },
  { max: Infinity, color: '--ord5', label: '75% and over' },
];""",
     """const BANDS = [
  { max: 10, color: '--ovr1', label: 'Under 10%' },
  { max: 30, color: '--ovr2', label: '10 to 30%' },
  { max: 50, color: '--ovr3', label: '30 to 50%' },
  { max: 75, color: '--ovr4', label: '50 to 75%' },
  { max: Infinity, color: '--ovr5', label: '75% and over' },
];

// Narrowing to a tier asks a different question of the same chart: not "how much
// of this group's work pays enough" but "how much of the work it enters people
// into at this credential does". The roll-up happens after the filter for that
// reason, and the caption changes with it.
const CREDS = [{ id: 'all', label: 'All credentials' }].concat(
  TIER_ORDER.map((t) => ({ id: t, label: t }))
);

// The table could always sort by any column. The chart could only rank by size,
// which is the one measure on it that is not the finding.
const SORTS = [
  { id: 'jobs', label: 'Jobs' },
  { id: 'below', label: 'Share below' },
];"""),

    ("""  const pool = pricedPool(LC.allOcc);
  const head = rollUp(pool, LWA);
  const groups = rollUpBy(pool, (o) => o.f, LWA).sort((a, b) => b.jobs - a.jobs);""",
     """  const pool = pricedPool(LC.allOcc);
  const head = rollUp(pool, LWA);"""),

    # ---- the whole panel moves inside the two pickers --------------------
    ("""      <LwPicker value={lw} onChange={setLw} />

      <Panel
        title="What Vermont does for a living, and how much of it pays enough"
        note={marketShape(groups, head ? head.jobs : TOTJ)}
        cap={`Bar length is jobs. Shading is the share of that group’s jobs paying below a living wage for ${lw}, read off each occupation’s own pay distribution rather than from its median. Click any bar for the occupations inside it.`}
        src={`Vermont occupation data, 2025 · ${fmt(head ? head.jobs : 0)} jobs with a published pay distribution · benchmark ${money(LWA)} a year (${lw})`}
        data={{""",
     """      <LwPicker value={lw} onChange={setLw} />

      <PickerPair id="ov-rows" aLabel="Credential" a={CREDS} bLabel="Sort by" b={SORTS}>
        {(tier, sort) => {
          const sub = tier === 'all' ? pool : pool.filter((o) => o.t === tier);
          const subHead = rollUp(sub, LWA);
          const groups = rollUpBy(sub, (o) => o.f, LWA).sort((a, b) =>
            sort === 'below' ? b.below - a.below : b.jobs - a.jobs
          );
          const scope = tier === 'all' ? '' : ` entered at ${tier.toLowerCase()}`;
          return (
      <Panel
        title="What Vermont does for a living, and how much of it pays enough"
        note={marketShape(groups, subHead ? subHead.jobs : TOTJ)}
        cap={`Bar length is jobs${scope}. Shading is the share of that group’s jobs${scope} paying below a living wage for ${lw}, read off each occupation’s own pay distribution rather than from its median. Click any bar for the occupations inside it.`}
        src={`Vermont occupation data, 2025 · ${fmt(subHead ? subHead.jobs : 0)} jobs with a published pay distribution${scope} · benchmark ${money(LWA)} a year (${lw})`}
        data={{"""),

    ("""          rows: groups,
          label: 'vermont-at-a-glance',
          initialSort: { k: 'jobs', dir: -1 },
          unit: 'occupation groups',
        }}""",
     """          rows: groups,
          label: 'vermont-at-a-glance',
          initialSort: { k: sort === 'below' ? 'below' : 'jobs', dir: -1 },
          unit: 'occupation groups',
        }}"""),

    ("""                aria:
                  'Vermont employment by occupation group, shaded by how much of it pays below a living wage',
              }}
            />
          )}
        </Split>
      </Panel>
    </>
  );
}""",
     """                aria:
                  'Vermont employment by occupation group, shaded by how much of it pays below a living wage',
              }}
            />
          )}
        </Split>
      </Panel>
          );
        }}
      </PickerPair>
    </>
  );
}"""),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("Overview.js: %d occurrences of %r" % (s.count(old), old[:70]))

for old, new in subs:
    s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)

for old, new, _ in css_subs:
    css = css.replace(old, new)
io.open(CSS, "w", encoding="utf-8", newline="").write(css)

print("Overview.js patched, %d bytes" % len(s))
print("globals.css patched, %d bytes" % len(css))
