import { useCallback, useEffect, useState } from 'react';
import { HowTo, LwPicker, Panel } from '../ui';
import { FORMATS, SCOPE_KINDS, CAVEATS, SOURCES, buildReport, scopeOptions } from '@/lib/report';
import { LC } from '@/lib/data';
import { fmt, money } from '@/lib/format';

/**
 * The report tab: pick a format, a scope and a benchmark, and read the output.
 *
 * WHY THE WHOLE REPORT IS ON SCREEN
 * ---------------------------------
 * The reader of this report is not the person operating the dashboard. It is
 * whoever they send it to -- a board, a campus, a legislator -- who will never
 * open a filter. So the person generating it has to be able to see exactly what
 * they are about to send, including the caveats, before they send it. A button
 * that produced a file without showing it would make the operator the only
 * person who never reads the thing.
 *
 * Both formats are the same findings. The one-pager stacks them; the deck gives
 * each one a frame and a line to say aloud. Neither adds a sentence the other
 * does not have.
 *
 * ON THE WRITING
 * --------------
 * Every sentence here and in lib/report.js is a figure or a comparison between
 * figures. Nothing grades what it describes, because the report leaves the tool
 * and cannot be checked against it; scripts/check_report_language.py enforces
 * that against a word list rather than leaving it to whoever edits next.
 */

function useSticky(key, fallback) {
  const [v, setV] = useState(fallback);
  useEffect(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored) setV(stored);
    } catch (e) {
      /* blocked storage — keep the default */
    }
  }, [key]);
  const set = useCallback(
    (next) => {
      setV(next);
      try {
        localStorage.setItem(key, next);
      } catch (e) {
        /* non-fatal */
      }
    },
    [key]
  );
  return [v, set];
}

function Chips({ label, options, value, onPick, id }) {
  return (
    <div className="rankctl">
      <span className="sclab">{label}</span>
      <div className="chips">
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            id={id ? id + '-' + o.id : undefined}
            className={o.id === value ? 'on' : undefined}
            aria-pressed={o.id === value}
            onClick={() => onPick(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/** To-scale rows. The value is printed on every row, so no row needs the axis. */
function Bars({ rows, twoCol }) {
  if (!rows || !rows.length) return null;
  return (
    <div className={twoCol ? 'rbars two' : 'rbars'}>
      {rows.map((r, i) => (
        <div className="rbar" key={r.label + i}>
          <span className="rbl">{r.label}</span>
          <span className="rtrk">
            <span
              className="rfil"
              style={{
                width: Math.max(0, Math.min(100, r.pct)) + '%',
                background: 'var(' + (r.color || '--s1') + ')',
              }}
            />
          </span>
          <span className="rbv num">{r.value}</span>
        </div>
      ))}
    </div>
  );
}

function Grid({ table }) {
  if (!table) return null;
  return (
    <div className="rtblwrap">
      <table className="rtbl">
        <thead>
          <tr>
            {table.cols.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((r, i) => (
            <tr key={i}>
              {r.map((cell, j) => (
                <td key={j}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Stats({ stats }) {
  if (!stats || !stats.length) return null;
  return (
    <div className="rstats">
      {stats.map(([v, k]) => (
        <div className="rstat" key={k}>
          <div className="rv num">{v}</div>
          <div className="rk">{k}</div>
        </div>
      ))}
    </div>
  );
}

/**
 * One finding.
 *
 * A table of more than four columns cannot be read in a half-width track, so it
 * takes both. The wrapper scrolls on screen either way, which is exactly why
 * this has to be decided here: a scrollbar hides the overflow from whoever
 * generates the report, and loses the columns for whoever prints it.
 */
function Finding({ f, n }) {
  // Four columns was still 16px too wide for a half track at 1500px, so the
  // threshold is three: a table of four or more takes the full width.
  const wide = !!(f.table && f.table.cols.length > 3);
  return (
    <div className={wide ? 'rfnd wide' : 'rfnd'}>
      <h4>
        <span className="rn">{String(n).padStart(2, '0')}</span>
        {f.head}
      </h4>
      <Stats stats={f.stats} />
      {(f.body || []).map((p, i) => (
        <p key={i}>{p}</p>
      ))}
      <Bars rows={f.bars} twoCol={f.twoCol} />
      <Grid table={f.table} />
      {f.read ? <p className="rread">{f.read}</p> : null}
      {f.src ? <p className="rsrc">{f.src}</p> : null}
    </div>
  );
}

function Brief({ rep }) {
  return (
    <div className="rpage">
      <div className="rhead">
        <div className="rkick">
          <span>{rep.title}</span>
          <span>
            {'Benchmark: ' + rep.benchmark + ' — ' + money(rep.floor) + '/yr'}
          </span>
        </div>
        <h3>{rep.title + ': what the figures show'}</h3>
        <p className="rstand">{rep.standfirst}</p>
      </div>

      {rep.strip && rep.strip.length ? (
        <div className="rstrip">
          {rep.strip.map(([v, k]) => (
            <div className="rcell" key={k}>
              <div className="rv num">{v}</div>
              <div className="rk">{k}</div>
            </div>
          ))}
        </div>
      ) : null}

      <div className="rfnds">
        {rep.findings.map((f, i) => (
          <Finding key={f.id} f={f} n={i + 1} />
        ))}
      </div>

      <div className="rfoot">
        <p>
          <b>Sources.</b> {SOURCES}
        </p>
        {CAVEATS.map((c, i) => (
          <p key={i}>{c}</p>
        ))}
      </div>
    </div>
  );
}

function Slides({ rep }) {
  const [at, setAt] = useState(0);
  const total = rep.findings.length + 2;
  const show = useCallback((i) => setAt(Math.max(0, Math.min(total - 1, i))), [total]);

  // A scope change can leave the viewer past the end of a shorter report.
  useEffect(() => {
    setAt(0);
  }, [rep.title, rep.benchmark]);

  const slide = (i, body) => (
    <article className={i === at ? 'rslide' : 'rslide off'} key={i} aria-hidden={i !== at}>
      {body}
    </article>
  );

  const frames = [];

  frames.push(
    slide(
      0,
      <>
        <div className="rsk">Vermont Labor Market Overview</div>
        <h3>{rep.title}</h3>
        <p className="rthesis">{rep.standfirst}</p>
        <div className="rmeta">
          {rep.sub} · Benchmark: {rep.benchmark} at {money(rep.floor)} a year
          <br />
          Vermont State Colleges System &amp; Strada Education Foundation
        </div>
      </>
    )
  );

  rep.findings.forEach((f, i) => {
    frames.push(
      slide(
        i + 1,
        <>
          <div className="rsk">{'Finding ' + String(i + 1).padStart(2, '0')}</div>
          <h3>{f.head}</h3>
          <div className="rbody">
            <Stats stats={f.stats} />
            {(f.body || []).map((p, n) => (
              <p key={n}>{p}</p>
            ))}
            <Bars rows={f.bars} twoCol={f.twoCol} />
            <Grid table={f.table} />
          </div>
          {f.read ? <div className="rread">{f.read}</div> : null}
          <div className="rsrc">{f.src}</div>
        </>
      )
    );
  });

  frames.push(
    slide(
      total - 1,
      <>
        <div className="rsk">What these figures rest on</div>
        <h3>How to read the numbers in this deck</h3>
        <div className="rbody">
          <div className="rpills">
            {CAVEATS.map((c, i) => (
              <div className="rpill" key={i}>
                {c}
              </div>
            ))}
          </div>
        </div>
        <div className="rsrc">{SOURCES}</div>
      </>
    )
  );

  return (
    <div className="rdeck">
      <div className="rstage">{frames}</div>
      <div className="rdeckbar">
        <button type="button" className="sldbtn" onClick={() => show(at - 1)} disabled={at === 0}>
          ← Back
        </button>
        <button
          type="button"
          className="sldbtn"
          onClick={() => show(at + 1)}
          disabled={at === total - 1}
        >
          Next →
        </button>
        <div className="rdots">
          {Array.from({ length: total }, (_, i) => (
            <button
              key={i}
              type="button"
              className="rdot"
              aria-current={i === at ? 'true' : 'false'}
              aria-label={'Slide ' + (i + 1)}
              onClick={() => show(i)}
            >
              {i + 1}
            </button>
          ))}
        </div>
        <span className="rcount num">{'Slide ' + (at + 1) + ' of ' + total}</span>
      </div>
    </div>
  );
}

export default function Report({ lw, setLw }) {
  const [format, setFormat] = useSticky('vt-rpt-format', 'brief');
  const [kind, setKind] = useSticky('vt-rpt-kind', 'vt');
  const [picked, setPicked] = useSticky('vt-rpt-pick-' + kind, '');

  const opts = scopeOptions(kind);
  const pick = opts.some((o) => o.id === picked) ? picked : opts.length ? opts[0].id : null;
  const fmtId = FORMATS.some((f) => f.id === format) ? format : 'brief';
  const kindId = SCOPE_KINDS.some((k) => k.id === kind) ? kind : 'vt';

  const rep = buildReport(kindId, pick, lw);

  return (
    <>
      <HowTo>
        A report built for someone who will not open this dashboard. Pick what it covers and which
        household it measures pay against; every figure comes from the same data the other tabs
        show, and the figures are worked out when you choose, not written in advance. Print it, or
        save it as a PDF, with the button below.
      </HowTo>

      <div className="rptctl">
        <Chips
          id="rpt-format"
          label="Format"
          options={FORMATS}
          value={fmtId}
          onPick={setFormat}
        />
        <Chips id="rpt-scope" label="Scope" options={SCOPE_KINDS} value={kindId} onPick={setKind} />
        {opts.length ? (
          <div className="ctrls">
            <label htmlFor="rpt-pick">
              <span>{SCOPE_KINDS.filter((k) => k.id === kindId)[0].label}</span>
              <select id="rpt-pick" value={pick || ''} onChange={(e) => setPicked(e.target.value)}>
                {opts.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        ) : null}
        <LwPicker value={lw} onChange={setLw} />
        <div className="rptgo">
          <button
            type="button"
            className="rptprint"
            onClick={() => {
              if (typeof window !== 'undefined') window.print();
            }}
          >
            Print or save as PDF
          </button>
          <span className="ctrlnote">
            {rep.findings.length + ' findings · ' + (fmtId === 'brief' ? 'one page' : rep.findings.length + 2 + ' slides')}
          </span>
        </div>
      </div>

      <Panel
        title={'Report preview — ' + rep.title}
        cap={
          'This is the whole output. What you see here is what prints, caveats included, so ' +
          'nothing reaches a reader that you have not read first.'
        }
        src={
          'Benchmark ' +
          rep.benchmark +
          ' · $' +
          LC.livingWage[rep.benchmark].toFixed(2) +
          '/hr at ' +
          fmt(LC.hours) +
          ' hours'
        }
      >
        <div className={fmtId === 'brief' ? 'rpt rpt-brief' : 'rpt rpt-slides'} id="rpt-out">
          {fmtId === 'brief' ? <Brief rep={rep} /> : <Slides rep={rep} />}
        </div>
      </Panel>
    </>
  );
}
