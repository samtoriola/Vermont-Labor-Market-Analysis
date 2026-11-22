"""Pathways / By credential level: the programme overlap the review asked for.

"Add program filter to see overlap by CIP." The overlap worth seeing is between
a VSCS programme and the credential ladder this section is built on: a programme
produces graduates, the crosswalk links it to occupations, and those occupations
are entered at particular rungs. A programme whose occupations sit on three
different rungs is a real fact about the programme.

sow.json now carries tierMix per programme -- graduates attributed per entry
tier, out of the same employment-weighted allocation as everything else on the
VSCS tab, so this panel and the alignment tab cannot disagree.

A SEPARATE PANEL, not a filter on the chart above it. The chart above counts
JOBS by the credential they ask for; this counts GRADUATES by the credential the
work they feed asks for. Filtering one with the other would put two units on one
mark, which is the rule this dashboard keeps hardest.

Two honest edges the panel states rather than hides:
  - a programme can link to no Vermont occupation at all (Liberal Arts, 123
    completions, links to one SOC that is not entered at a listed tier), and
    then there is no overlap to draw
  - the tiers a programme touches are the tiers of the occupations its CIP maps
    to, not a claim about what the programme itself awards. That is degree type,
    and it lives on VSCS alignment.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "components", "views", "Q4.js")
s = io.open(P, encoding="utf-8").read()

subs = [
    ("""import {
  DATA, LC, TIER_ORDER, SERIES,
  lwAnnual, occByTier, credentialFunnel,
} from '@/lib/data';""",
     """import { useState } from 'react';
import {
  DATA, LC, SOW, TIER_ORDER, SERIES,
  lwAnnual, occByTier, credentialFunnel,
} from '@/lib/data';"""),

    # ---- the panel --------------------------------------------------------
    ("""export default function Q4({ lw, setLw, section }) {""",
     """/**
 * One VSCS programme against the credential ladder.
 *
 * The select rather than chips: there are 149 programmes and the reader is
 * looking one up, not comparing a handful. Ordered by size, because the ones
 * worth opening first are the ones with graduates in them.
 */
function ProgramOverlap() {
  const progs = (SOW.vscs.byCip || []).filter((p) => p.c > 0);
  const [cip, setCip] = useState(progs.length ? progs[0].cip : null);
  if (!progs.length) return null;
  const p = progs.filter((x) => x.cip === cip)[0] || progs[0];
  const mix = p.tierMix || {};
  const tiers = TIER_ORDER.filter((t) => mix[t]);
  const placed = tiers.reduce((a, t) => a + mix[t], 0);

  return (
    <Panel
      title="Where does one programme's output land on the ladder?"
      cap={
        `Graduates attributed to each entry credential, for one VSCS programme. These are the ` +
        `credentials the WORK asks for, not the award the programme grants — a certificate ` +
        `programme can feed occupations entered at a bachelor's, and several do. The split is ` +
        `the same employment-weighted allocation the VSCS alignment tab uses, so it is modelled ` +
        `rather than observed.`
      }
      src={`Federal completions data, 2024 · ${fmt(progs.length)} programmes · CIP-to-SOC crosswalk · Vermont occupation data, 2025`}
      data={{
        cols: [
          { k: 'n', label: 'Programme', kind: 'text', get: (r) => r.n },
          { k: 'cip', label: 'CIP code', kind: 'text', get: (r) => r.cip },
          { k: 'c', label: 'Completions', kind: 'num1', get: (r) => r.c },
          { k: 'linked', label: 'Graduates attributed', kind: 'num1', get: (r) => r.linked },
          { k: 'nsoc', label: 'Occupations linked', kind: 'num', get: (r) => r.nsoc },
          ...TIER_ORDER.map((t) => ({
            k: 'tm_' + t, label: t, kind: 'num1',
            get: (r) => (r.tierMix || {})[t] || null,
          })),
        ],
        rows: progs,
        label: 'vscs-programmes-by-credential',
        initialSort: { k: 'c', dir: -1 },
        unit: 'programmes',
      }}
    >
      <div className="ctrls">
        <label htmlFor="cip-select">
          <span>Programme</span>
          <select id="cip-select" value={p.cip} onChange={(e) => setCip(e.target.value)}>
            {progs.map((x) => (
              <option key={x.cip} value={x.cip}>
                {x.n.replace(/\\.$/, '')} — {x.c.toFixed(0)}
              </option>
            ))}
          </select>
        </label>
        <span className="ctrlnote">
          {fmt(p.c)} completions · {p.nsoc ? `${fmt(p.nsoc)} linked occupations` : 'no linked occupation in Vermont'}
        </span>
      </div>
      {tiers.length ? (
        <>
          <ol className="plist">
            {tiers.map((t) => (
              <li key={t}>
                <span className="pn">{t}</span>
                <span className="pv">{mix[t].toFixed(1)}</span>
              </li>
            ))}
          </ol>
          <p className="cap" style={{ margin: '10px 0 0' }}>
            {placed.toFixed(1)} of this programme&rsquo;s {fmt(p.c)} completions land in a Vermont
            occupation with a listed entry credential
            {tiers.length > 1
              ? `, spread across ${tiers.length} rungs — which is the overlap: one programme is not one rung.`
              : ', all on one rung.'}
          </p>
        </>
      ) : (
        <p className="cap" style={{ margin: 0 }}>
          The crosswalk links this programme to no Vermont occupation carrying an entry
          credential, so there is no rung to place its graduates on. Its completions are
          still counted in the 1,983 total.
        </p>
      )}
    </Panel>
  );
}

export default function Q4({ lw, setLw, section }) {"""),

    # ---- hang it under the section ----------------------------------------
    ("""                  occupations at that level.
                </HowTo>
                <Picker id="q4-cred" label="Measure" options={CRED_MEASURES}>""",
     """                  occupations at that level. The panel underneath takes one VSCS
                  programme and shows which rungs its graduates reach.
                </HowTo>
                <Picker id="q4-cred" label="Measure" options={CRED_MEASURES}>"""),
]

for old, _ in subs:
    if s.count(old) != 1:
        raise SystemExit("Q4.js: %d occurrences of %r" % (s.count(old), old[:70]))
for old, new in subs:
    s = s.replace(old, new)

# The panel goes at the end of the by-credential-level section, after the Picker.
anchor = """                </Picker>
              </>
            ),
          },"""
if s.count(anchor) < 1:
    raise SystemExit("could not find the section close")
first = s.index(anchor)
s = s[:first] + """                </Picker>
                <ProgramOverlap />
              </>
            ),
          },""" + s[first + len(anchor):]

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("Q4.js patched, %d bytes" % len(s))
