'use client';

import { DATA, LC, PCT, TIER_ORDER, SERIES, lwAnnual, occByTier } from '@/lib/data';
import { fmt, money } from '@/lib/format';
import { Answer, Callout, Panel, Table, VHead, LwPicker, N, DrillHint } from '../ui';
import { ActiveFilters } from '../Filters';
import { useDrill, occDrill } from '../Drill';
import { RankedBars, BoxPlot, BoxLegend } from '../charts';

export default function Q4({ lw, setLw }) {
  const LWA = lwAnnual(lw);
  const { open } = useDrill();

  const tierDrill = (k) =>
    open(
      occDrill({
        label: 'Entry credential',
        title: k,
        cap: 'Every occupation whose typical entry credential is this tier, largest first.',
        occ: occByTier(k),
        lwAnnual: LWA,
      })
    );
  const t = {};
  LC.tiers.forEach((r) => {
    t[r.t] = r;
  });
  const sub = t['Sub-baccalaureate'];
  const ba = t["Bachelor's"];
  const hs = t['High school'];
  const nfc = t['No formal credential'];
  const grad = t['Graduate / professional'];
  const lastCps = DATA.trend[DATA.trend.length - 1];
  const P = PCT.tiers;

  const tierBox = TIER_ORDER.filter((k) => P[k]).map((k, i) => {
    const b = P[k];
    const r = t[k];
    return {
      label: k,
      p10: b.p10,
      p25: b.p25,
      p50: b.p50,
      p75: b.p75,
      p90: b.p90,
      color: SERIES[i],
      extra: [
        ['Jobs', fmt(r.jobs)],
        ['Share of employment', r.share + '%'],
        ['Above living wage', r.above[lw].toFixed(1) + '%'],
        ['Occupations', fmt(b.nocc)],
      ],
    };
  });

  return (
    <>
      <VHead
        title="Education pathways"
      >
        The share of Vermont employment at each entry credential, and how those requirements relate to earnings.
      </VHead>

      <ActiveFilters />

      <Answer>
        <p>
          By typical entry credential, Vermont employment splits: <strong>high school</strong>{' '}
          <N>{hs.share.toFixed(1)}%</N>, <strong>bachelor&rsquo;s</strong>{' '}
          <N>{ba.share.toFixed(1)}%</N>, <strong>no formal credential</strong>{' '}
          <N>{nfc.share.toFixed(1)}%</N>, <strong>sub-baccalaureate</strong>{' '}
          <N>{sub.share.toFixed(1)}%</N>, and <strong>graduate or professional</strong>{' '}
          <N>{grad.share.toFixed(1)}%</N>.
        </p>
        <p>
          <strong>Earnings rise with the credential at every percentile</strong> &mdash; but the
          steps are very unequal, and the percentile view is what reveals that. From high school to
          sub-baccalaureate the median moves only{' '}
          <N>{money(P['Sub-baccalaureate'].p50 - P['High school'].p50)}</N> (
          <N>{((P['Sub-baccalaureate'].p50 / P['High school'].p50 - 1) * 100).toFixed(0)}%</N>), and
          the two distributions overlap heavily. From sub-baccalaureate to bachelor&rsquo;s it jumps{' '}
          <N>{money(P["Bachelor's"].p50 - P['Sub-baccalaureate'].p50)}</N> (
          <N>{((P["Bachelor's"].p50 / P['Sub-baccalaureate'].p50 - 1) * 100).toFixed(0)}%</N>). The
          ladder is real, but its rungs are not evenly spaced.
        </p>
        <p>
          <strong>This qualifies the living-wage figures.</strong> The share of jobs clearing the
          benchmark climbs from <N>{hs.above[lw].toFixed(0)}%</N> at high school to{' '}
          <N>{sub.above[lw].toFixed(0)}%</N> at sub-baccalaureate &mdash; a large-looking gain
          driven by a modest shift in the distribution. The sub-baccalaureate 25th percentile sits
          at <N>{money(P['Sub-baccalaureate'].p25)}</N>, almost exactly on the {money(LWA)}{' '}
          benchmark, so a small move in the distribution flips a lot of jobs across the line. Read
          it as a threshold effect, not a pay premium: roughly a quarter of sub-baccalaureate jobs
          still fall below self-sufficiency.
        </p>
        <p>
          <strong>Where that leaves VSCS.</strong> Sub-baccalaureate is the smallest tier by
          employment (<N>{sub.share.toFixed(1)}%</N>) and its earnings advantage over high school is
          real but narrow. The decisive wage step is the bachelor&rsquo;s threshold. A credential
          strategy justified on earnings grounds points at bachelor&rsquo;s-level pathways or at the
          specific sub-baccalaureate occupations whose own distributions sit well above the tier
          median &mdash; not at the sub-baccalaureate tier as a whole.
        </p>
      </Answer>

      <LwPicker value={lw} onChange={setLw} />

      <Panel
        title="The credential ladder, with spread"
        cap="Click a tier to list its occupations. Earnings distribution at each entry-credential tier. Note how far the high-school and sub-baccalaureate boxes overlap, and how the bachelor's box separates from both — that asymmetry is the finding, and a median-only chart conceals it."
        src="Lightcast · employment-weighted mean of occupation percentiles · 100% of jobs priced"
      >
        <BoxLegend />
        <BoxPlot
          rows={tierBox}
          opts={{
            labelWidth: 200,
            rule: LWA,
            ruleLabel: 'Living wage ' + money(LWA),
            endLabels: true,
            aria: 'Earnings percentile distribution by entry-credential tier',
          }}
        />
      </Panel>

      <Panel
        title="The credential ladder in full"
        cap={`Employment, the full wage distribution, and demand at each tier. Benchmark: ${lw}.`}
        src="Lightcast · Typical Entry Level Education, jobs-weighted"
      >
        <Table
          cols={[
            'Entry credential',
            'Jobs',
            'Share',
            '10th',
            '25th',
            'Median',
            '75th',
            '90th',
            'Above living wage',
            'Annual openings',
          ]}
          rows={TIER_ORDER.map((k) => {
            const r = t[k];
            const b = P[k] || {};
            return {
              cells: [
                r.t,
                fmt(r.jobs),
                r.share + '%',
                money(b.p10),
                money(b.p25),
                money(b.p50),
                money(b.p75),
                money(b.p90),
                r.above[lw].toFixed(1) + '%',
                fmt(r.open),
              ],
            };
          })}
        />
      </Panel>

      <div className="grid2">
        <Panel
          title="Share of employment"
          cap="Where Vermont's jobs sit on the credential ladder."
          src={`Lightcast · ${fmt(LC.totalJobs)} jobs`}
        >
          <RankedBars
            rows={TIER_ORDER.map((k, i) => {
              const r = t[k];
              return {
                label: r.t,
                value: r.share,
                color: SERIES[i],
                mode: 'pct',
                extra: [
                  ['Jobs', fmt(r.jobs)],
                  ['Occupations', fmt(r.nocc)],
                ],
              };
            })}
            opts={{
              mode: 'pct',
              labelWidth: 176,
              width: 470,
              valueLabel: 'Share of jobs',
              aria: 'Employment share by credential tier',
            }}
          />
        </Panel>

        <Panel
          title="Earnings dispersion"
          cap="The 90th percentile divided by the 10th. Higher means a wider range of outcomes for the same entry credential — more upside, but also more variance in where a graduate lands."
          src="Lightcast · ratio of 90th to 10th percentile"
        >
          <RankedBars
            rows={TIER_ORDER.filter((k) => P[k]).map((k, i) => {
              const b = P[k];
              return {
                label: k,
                value: b.p90 / b.p10,
                color: SERIES[i],
                dec: 2,
                extra: [
                  ['10th percentile', money(b.p10)],
                  ['90th percentile', money(b.p90)],
                  ['Median', money(b.p50)],
                ],
              };
            })}
            opts={{
              dec: 2,
              labelWidth: 176,
              width: 470,
              valueLabel: 'p90 ÷ p10',
              aria: 'Earnings dispersion by credential tier',
            }}
          />
        </Panel>
      </div>

      <Panel
        title="Share of jobs paying above the living wage"
        cap={`The wage-quality payoff to each credential tier. Benchmark: ${lw} at ${money(LWA)}/yr — change it above.`}
        src="Lightcast · MIT Living Wage 2025 · occupation median vs benchmark"
      >
        <RankedBars
          rows={TIER_ORDER.map((k, i) => {
            const r = t[k];
            return {
              label: r.t,
              value: r.above[lw],
              color: SERIES[i],
              mode: 'pct',
              extra: [
                ['Jobs', fmt(r.jobs)],
                ['Median earnings', money(r.med)],
              ],
            };
          })}
          opts={{
            mode: 'pct',
            labelWidth: 176,
            max: 100,
            valueLabel: 'Above living wage',
            aria: 'Living-wage share by credential tier',
          }}
        />
      </Panel>

      <Panel
        title="All eight credential categories"
        cap="The five SOW tiers unpacked into the credential labels Lightcast actually assigns. Sub-baccalaureate is three distinct categories, and the certificate route (postsecondary nondegree award) is the largest of them."
        src="Lightcast · 2 of 798 occupations carry no education assignment"
      >
        <Table
          cols={[
            'Lightcast entry credential',
            'SOW tier',
            'Jobs',
            'Share',
            'Median earnings',
            'Occupations',
          ]}
          rows={LC.eduDetail.map((r) => ({
            cells: [r.e, r.tier, fmt(r.jobs), r.share + '%', r.med ? money(r.med) : '—', fmt(r.nocc)],
          }))}
        />
      </Panel>

      <Callout label="Read this against attainment">
        <p>
          These are job <em>requirements</em>. Vermont worker <em>attainment</em> sits well above
          them: <N>{(ba.share + grad.share).toFixed(1)}%</N> of jobs ask for a bachelor&rsquo;s or
          more, while <N>{lastCps.ba.toFixed(1)}%</N> of workers 25+ hold one. A program strategy
          built only on the requirement side understates the credential level Vermont employers
          actually get in their applicant pool; one built only on the attainment side overstates
          what the jobs demand. The{' '}
          <N>{(lastCps.ba - ba.share - grad.share).toFixed(1)}-point</N> gap is the space where
          underemployment lives, and it is worth a dedicated cut before any program decision.
        </p>
      </Callout>
    </>
  );
}
