"""Option C: the alignment ratio against the openings that ask for a credential.

build_sow.py already computes this denominator, and its own comment says why --
"comparing VSCS output to ALL openings understates alignment, because most
Vermont openings are in occupations needing no formal credential". The total
reaches sow.json as vscs.openCred. The chart never used it. Throwaway.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))


def edit(rel, pairs):
    p = os.path.join(H, "..", rel)
    s = io.open(p, encoding="utf-8").read()
    for old, _ in pairs:
        assert s.count(old) == 1, "%s: %d occurrences of %r" % (rel, s.count(old), old[:70])
    for old, new in pairs:
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
    print(rel, "patched,", len(s), "bytes")


# ---- the denominator, where the other dataset-level helpers live ------------
edit("lib/data.js", [(
    "export function occByFamily(",
    '''/**
 * The entry credentials VSCS awards into.
 *
 * Kept in step with CRED in scripts/build_sow.py, which uses the same three to
 * compute SOW.vscs.openCred. Certificates and associate degrees land at
 * sub-baccalaureate; bachelor's and master's at their own levels.
 */
export const VSCS_TIERS = ['Sub-baccalaureate', "Bachelor's", 'Graduate / professional'];

/**
 * Annual openings per occupation group in work that asks for one of those.
 *
 * The alignment chart divides VSCS graduates by openings, and dividing by ALL of
 * an occupation group's openings asks VSCS to supply work a college is not the
 * route into: 6,065 food preparation openings a year, 4,190 in sales. Measured
 * that way the whole system reads 3.5% and five groups read as zero. Against the
 * openings that actually ask for a credential it awards the same production reads
 * 9.7%, and three of those five turn out to have no such openings at all -- which
 * is not a gap, it is a different kind of work.
 *
 * Computed once: it depends on nothing the reader can change.
 */
let credOpenCache = null;
export function credOpenByFamily() {
  if (credOpenCache) return credOpenCache;
  const by = {};
  LC.allOcc.forEach((o) => {
    if (!by[o.f]) by[o.f] = 0;
    if (VSCS_TIERS.includes(o.t)) by[o.f] += o.o || 0;
  });
  credOpenCache = by;
  return by;
}

export function occByFamily('''
)])

# ---- the read-out ----------------------------------------------------------
edit("lib/insight.js", [(
    "/** The largest single credential category inside the tiers. */",
    '''/**
 * Occupation groups with work that asks for a VSCS credential and no VSCS
 * graduates reaching it.
 *
 * Replaces familiesNoCompletions(), which counted every group with no graduates
 * against ALL openings -- five of them, four of which have no credential-requiring
 * openings at all. Food preparation drawing a zero is not a finding. Legal drawing
 * one is.
 */
export function credGap(rows) {
  const bare = rows.filter((r) => r.openCred > 0 && !r.linked);
  const total = rows.reduce((a, r) => a + r.openCred, 0);
  const linked = rows.reduce((a, r) => a + r.linked, 0);
  const overall = total ? (linked / total) * 100 : 0;
  const lead = rows
    .filter((r) => r.openCred > 0 && r.linked)
    .slice()
    .sort((a, b) => b.linked / b.openCred - a.linked / a.openCred)[0];
  const head =
    `Across every occupation group, VSCS graduates a number equal to ${overall.toFixed(1)}% of ` +
    `the ${fmt(total)} openings a year that ask for a credential it awards` +
    (lead
      ? `, and ${((lead.linked / lead.openCred) * 100).toFixed(0)}% in ${shortLabel(lead.f)}.`
      : '.');
  if (!bare.length) return found(head);
  const names = bare.map((r) => shortLabel(r.f));
  return found(
    head +
    ` ${names.length === 1 ? names[0] : names.slice(0, -1).join(', ') + ' and ' + names[names.length - 1]} ` +
    `${names.length === 1 ? 'has' : 'have'} ${fmt(bare.reduce((a, r) => a + r.openCred, 0))} ` +
    `between them and no VSCS graduates at all.`
  );
}

/** The largest single credential category inside the tiers. */'''
)])

# ---- the chart -------------------------------------------------------------
edit("components/views/Q6.js", [
    ("import { SOW, SERIES, lwAnnual, occByFamily } from '@/lib/data';",
     "import { SOW, SERIES, lwAnnual, occByFamily, credOpenByFamily, VSCS_TIERS } from '@/lib/data';"),
    ("import { awardMix, familiesNoCompletions } from '@/lib/insight';",
     "import { awardMix, credGap } from '@/lib/insight';"),

    ("""  // Ordered by how far each occupation group's graduates go against its openings, with
  // the ones no graduate reaches at the foot rather than scattered through.
  const famShare = (r) => (r.open ? (r.linked / r.open) * 100 : null);

  const famAlign = V.byFamily
    .slice()
    .sort((a, b) => (famShare(b) || 0) - (famShare(a) || 0));""",
     """  /**
    * WHICH OPENINGS VSCS IS MEASURED AGAINST
    * ---------------------------------------
    * Not all of them. Dividing a group's graduates by every opening it has asks
    * VSCS to supply work a college is not the route into -- 6,065 food preparation
    * openings a year, 4,190 in sales -- and the chart then reads 3.5% overall with
    * five groups at zero. Against the openings whose entry credential is one VSCS
    * awards, the same production reads 9.7%, and three of those five turn out to
    * have no such openings at all.
    *
    * This is not a new measure. scripts/build_sow.py computes the total and its
    * own comment says why: "comparing VSCS output to ALL openings understates
    * alignment". It reaches the app as SOW.vscs.openCred and the chart had never
    * used it. All this does is split it by occupation group.
    */
  const CRED_OPEN = credOpenByFamily();
  const famRows = V.byFamily.map((r) => ({
    ...r,
    openCred: Math.round(CRED_OPEN[r.f] || 0),
    openAll: r.open,
  }));
  const famShare = (r) => (r.openCred ? (r.linked / r.openCred) * 100 : null);

  // Groups with no credential-requiring openings have nothing to divide by. They
  // are not a gap and must not be drawn as a zero beside groups that are, so they
  // come off the chart and are named under it.
  const famAlign = famRows
    .filter((r) => r.openCred > 0)
    .sort((a, b) => (famShare(b) || 0) - (famShare(a) || 0));
  const noCred = famRows
    .filter((r) => !r.openCred)
    .sort((a, b) => b.openAll - a.openAll);"""),

    ("""        extraStats: [
          ['Openings a year', fmt(r.open)],
          ['Graduates attributed', r.linked.toFixed(1)],
          [
            'Graduates as % of openings',
            famShare(r) === null ? '—' : famShare(r).toFixed(1) + '%',
          ],
        ],""",
     """        extraStats: [
          ['Openings asking for a VSCS credential', fmt(r.openCred)],
          ['All openings a year', fmt(r.openAll)],
          ['Graduates attributed', r.linked.toFixed(1)],
          [
            'Graduates as % of the openings that ask',
            famShare(r) === null ? '—' : famShare(r).toFixed(1) + '%',
          ],
        ],"""),

    ("""      stats: [
        [famShare(r) === null ? '—' : famShare(r).toFixed(1) + '%', 'Graduates vs openings'],
        [fmt(r.open), 'Openings a year'],
        [r.linked.toFixed(1), 'Graduates'],
      ],""",
     """      stats: [
        [famShare(r) === null ? '—' : famShare(r).toFixed(0) + '%', 'Of the openings that ask'],
        [fmt(r.openCred), 'Openings asking'],
        [r.linked.toFixed(1), 'Graduates'],
      ],"""),

    ("""                        note={familiesNoCompletions(V.byFamily)}
                        cap="Each occupation group's VSCS graduates measured against the openings it has each year. 25% means VSCS graduates a number equal to a quarter of the openings — not that it fills a quarter of them, which no figure here can tell you. Grey bars draw no VSCS graduates at all. Work that needs no credential sits there by nature, because college is not the route into it. Hover for the counts; click for the occupations behind it."
                        src="Federal completions data, 2024, against Vermont openings · spread by employment\"""",
     """                        note={credGap(famRows)}
                        cap={`Each occupation group's VSCS graduates measured against the openings it has each year whose entry credential is one VSCS awards — ${fmt(V.openCred)} of Vermont's ${fmt(V.openAll)} annual openings. 25% means VSCS graduates a number equal to a quarter of those openings, not that it fills a quarter of them, which no figure here can tell you. The openings column sits beside the bar because a high share of a small number is a different finding from a high share of a large one. Hover for the counts; click for the occupations behind it.`}
                        src={`Federal completions data, 2024, against Vermont openings asking for a sub-baccalaureate, bachelor's or graduate credential · ${fmt(V.openCred)} openings a year · graduates spread by employment`}"""),

    ("""                          cols: [
                            { k: 'f', label: 'Occupation group', kind: 'text', get: (r) => r.f },
                            { k: 'open', label: 'Openings a year', kind: 'num', get: (r) => r.open },
                            { k: 'linked', label: 'Graduates attributed', kind: 'num1', get: (r) => r.linked },
                            {
                              k: 'ratio',
                              label: 'Graduates as % of openings',
                              kind: 'rate',
                              get: famShare,
                            },
                            { k: 'jobs', label: 'Jobs', kind: 'num', get: (r) => r.jobs },
                          ],
                          rows: famAlign,""",
     """                          cols: [
                            { k: 'f', label: 'Occupation group', kind: 'text', get: (r) => r.f },
                            { k: 'openCred', label: 'Openings asking for a VSCS credential', kind: 'num', get: (r) => r.openCred },
                            { k: 'linked', label: 'Graduates attributed', kind: 'num1', get: (r) => r.linked },
                            {
                              k: 'ratio',
                              label: 'Graduates as % of the openings that ask',
                              kind: 'rate',
                              get: famShare,
                            },
                            { k: 'openAll', label: 'All openings a year', kind: 'num', get: (r) => r.openAll },
                            {
                              k: 'ratioAll',
                              label: 'Against all openings',
                              kind: 'rate',
                              get: (r) => (r.openAll ? (r.linked / r.openAll) * 100 : null),
                            },
                            { k: 'jobs', label: 'Jobs', kind: 'num', get: (r) => r.jobs },
                          ],
                          // Every group, including the three with nothing to divide
                          // by -- the table is where the full list belongs.
                          rows: famRows,"""),

    ("""                              rows={pick.map((r) => ({
                                label: r.f,
                                value: famShare(r) || 0,
                                // Grey where no graduate reaches this work at all. It is not
                                // a low score, it is the absence of a pipeline, and the two
                                // should not look the same. Keyed off the graduates rather
                                // than the share, so this counts the same families the
                                // read-out under the chart does.
                                color: r.linked > 0 ? '--s1' : '--ink-3',
                                onClick: () => select(r.f),
                                active: active === r.f,
                                extra: [
                                  ['Openings a year', fmt(r.open)],
                                  ['Graduates attributed', r.linked.toFixed(1)],
                                  ['Jobs', fmt(r.jobs)],
                                ],
                              }))}
                              opts={{
                                mode: 'pct',
                                labelWidth: 236,
                                width,
                                valueLabel: 'Graduates as % of openings',
                                clickHint: 'Click for the occupations inside it',
                                aria: 'Graduates as a share of openings by occupation group',
                              }}""",
     """                              rows={pick.map((r) => ({
                                label: r.f,
                                value: famShare(r) || 0,
                                // Grey where work asks for a credential VSCS awards and
                                // no graduate reaches it. That is the absence of a
                                // pipeline rather than a low one, and the two should not
                                // look the same. The groups with nothing to divide by are
                                // off the chart entirely, named underneath.
                                color: r.linked > 0 ? '--s1' : '--ink-3',
                                right: fmt(r.openCred),
                                onClick: () => select(r.f),
                                active: active === r.f,
                                extra: [
                                  ['Openings asking for a VSCS credential', fmt(r.openCred)],
                                  ['All openings a year', fmt(r.openAll)],
                                  ['Against all openings', r.openAll ? ((r.linked / r.openAll) * 100).toFixed(1) + '%' : '—'],
                                  ['Graduates attributed', r.linked.toFixed(1)],
                                  ['Jobs', fmt(r.jobs)],
                                ],
                              }))}
                              opts={{
                                mode: 'pct',
                                dec: 0,
                                labelWidth: 236,
                                width,
                                keepFill: true,
                                valueLabel: 'Graduates as % of the openings that ask',
                                valueHead: 'SHARE',
                                rightHead: 'OPENINGS',
                                clickHint: 'Click for the occupations inside it',
                                aria:
                                  'Graduates as a share of the credential-requiring openings in each occupation group',
                              }}"""),

    ("""                        <Split items={famAlign} keyOf={(r) => r.f} detail={famDetail}>""",
     """                        <>
                        <Split items={famAlign} keyOf={(r) => r.f} detail={famDetail}>"""),

    ("""                          )}
                        </Split>
                      </Panel>""",
     """                          )}
                        </Split>
                        {noCred.length ? (
                          <p className="cap nocred">
                            Not on the chart: <strong>{noCred.map((r) => r.f).join(', ')}</strong>.
                            No opening in {noCred.length === 1 ? 'it' : 'them'} asks for a
                            credential VSCS awards — {fmt(noCred.reduce((a, r) => a + r.openAll, 0))}{' '}
                            openings a year between {noCred.length === 1 ? 'it' : 'them'} and none
                            to measure against. They are in the table below.
                          </p>
                        ) : null}
                        </>
                      </Panel>"""),

    ("""                  VSCS graduates measured against Vermont openings, at whichever grain you
                  pick: the 22 occupation groups, or occupation by occupation. A share here is
                  graduates as a percentage of openings — never the share of openings
                  filled, which no figure on this dashboard can tell you.""",
     """                  VSCS graduates measured against the Vermont openings that ask for a
                  credential it awards, at whichever grain you pick: the 22 occupation
                  groups, or occupation by occupation. A share here is graduates as a
                  percentage of those openings — never the share of openings filled,
                  which no figure on this dashboard can tell you."""),
])
