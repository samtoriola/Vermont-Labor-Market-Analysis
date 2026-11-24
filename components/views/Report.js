import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
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

/**
 * A slide is a fixed frame and a table is not, so a long one has to be cut
 * somewhere. It is cut here, out loud: the slide carries the first rows and its
 * source line says how many it is showing. Letting it overflow instead meant
 * the frame clipped it, which dropped rows with nothing on the slide admitting
 * it -- a source line reading "five highest and the lowest" above four rows.
 */
const SLIDE_ROWS = 5;

// The one-pager is one page, which is the point of it: a brief that runs to
// five is a document somebody has to be asked to read. So it keeps every
// finding and every "so what", and trims the evidence under them -- the rows
// and bars past the first few -- rather than dropping findings. The tabs hold
// the rest, and every trimmed figure says so on its own source line.
const BRIEF_ROWS = 3;
const BRIEF_BARS = 4;
// Four columns is what a half-width track holds. The columns are ordered with
// the label first and the measure the headline names next, so the ones that
// fall off the end are the supporting ones.
const BRIEF_COLS = 4;

function trimCols(table, cap) {
  if (!table || table.cols.length <= cap) return { table, note: null };
  return {
    table: {
      cols: table.cols.slice(0, cap),
      rows: table.rows.map((r) => r.slice(0, cap)),
    },
    note: 'showing ' + cap + ' of ' + table.cols.length + ' columns',
  };
}

function trimRows(table, cap, where) {
  if (!table || table.rows.length <= cap) return { table, note: null };
  return {
    table: { ...table, rows: table.rows.slice(0, cap) },
    note: 'showing ' + cap + ' of ' + table.rows.length + ' rows, ' + where,
  };
}

function trimForSlide(table) {
  return trimRows(table, SLIDE_ROWS, 'the rest are on the dashboard');
}

/**
 * Bars are trimmed out of the middle, never off the end.
 *
 * Every bar chart here is sorted and the line beside it names the two ends --
 * "ranges from 0.0% to 94.3%". Lopping the tail would leave the chart
 * contradicting the sentence under it, so the first and last rows always
 * survive and the cut comes from the middle, where it changes nothing the text
 * claims.
 */
function trimBars(rows, cap) {
  if (!rows || rows.length <= cap) return { rows, note: null };
  return {
    rows: rows.slice(0, cap - 1).concat([rows[rows.length - 1]]),
    note: 'showing ' + cap + ' of ' + rows.length + ', including both ends',
  };
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
  const col = trimCols(f.table, BRIEF_COLS);
  const cut = trimRows(col.table, BRIEF_ROWS, 'the rest are on the dashboard');
  const bar = trimBars(f.bars, f.twoCol ? BRIEF_BARS + 2 : BRIEF_BARS);
  // On screen a four-column table still needs the full width; on paper the
  // type is small enough that it flows into a track like everything else.
  const wide = !!(cut.table && cut.table.cols.length > 3);
  const src = [f.src, col.note, cut.note, bar.note].filter(Boolean).join(' · ');
  return (
    <div className={wide ? 'rfnd wide' : 'rfnd'}>
      <h4>
        <span className="rn">{String(n).padStart(2, '0')}</span>
        {f.head}
      </h4>
      {/* The stats row repeats a figure the chart under it already carries.
          On a page with room that is a useful anchor; on a page held to one
          it is the first thing that can go. */}
      {bar.rows || cut.table ? null : <Stats stats={f.stats} />}
      {/* No body paragraph here. It is the explanatory sentence -- what a
          replacement rate is, how the allocation works -- and at one page it is
          what the chart and the "so what" have to be paid for with. The deck
          carries it, and so does the tab the source line names. */}
      <Bars rows={bar.rows} twoCol={f.twoCol} />
      <Grid table={cut.table} />
      {f.read ? <p className="rread">{f.read}</p> : null}
      {src ? <p className="rsrc">{src}</p> : null}
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
  const fitRef = useRef(null);

  // A scope change can leave the viewer past the end of a shorter report.
  useEffect(() => {
    setAt(0);
  }, [rep.title, rep.benchmark]);

  /**
   * Shrink the slide body if it does not fit the frame.
   *
   * A slide is a fixed 16:9 box and its contents are not: eight benchmark bars
   * need more room than two, and a two-line headline eats a row's worth before
   * the body starts. The frame clips rather than scrolls, so without this the
   * overflow simply removed bars and table rows with nothing on the slide
   * admitting it -- a source line reading "five highest and the lowest" above
   * four rows.
   *
   * Capping rows is the first defence and is stated on the slide. This is the
   * second, for the cases a cap cannot predict, and it is bounded: below 0.72
   * the type stops being readable at the back of a room, and the slide is
   * better cut than shrunk further.
   */
  useLayoutEffect(() => {
    const inner = fitRef.current;
    if (!inner) return;
    const outer = inner.parentElement;
    inner.style.setProperty('--fit', '1');
    const room = outer.clientHeight;
    const need = inner.scrollHeight;
    // Four pixels of slack: a trailing margin on the last child is outside
    // scrollHeight, and sub-pixel rounding costs a little more.
    if (need > room - 4 && need > 0) {
      inner.style.setProperty('--fit', String(Math.max(0.72, (room - 4) / need)));
    }
  });

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
    const cut = trimForSlide(f.table);
    frames.push(
      slide(
        i + 1,
        <>
          <div className="rsk">{'Finding ' + String(i + 1).padStart(2, '0')}</div>
          <h3>{f.head}</h3>
          <div className="rbody">
            {/* i is the finding's index; this is slide i + 1, because the
                title slide is 0. Attaching the ref on `i === at` put it on a
                hidden slide, which measures zero and never scaled anything. */}
            <div className="rfit" ref={i + 1 === at ? fitRef : null}>
              {/* The stats row repeats a figure the chart beside it already
                  carries, which on a page is a useful anchor and on a slide is
                  the thing that pushes the chart out of the frame. */}
              {f.bars || f.table ? null : <Stats stats={f.stats} />}
              {(f.body || []).map((p, n) => (
                <p key={n}>{p}</p>
              ))}
              <Bars rows={f.bars} twoCol={f.twoCol} />
              <Grid table={cut.table} />
            </div>
          </div>
          {f.read ? <div className="rread">{f.read}</div> : null}
          <div className="rsrc">{cut.note ? f.src + ' · ' + cut.note : f.src}</div>
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
          <div className="rpills" ref={total - 1 === at ? fitRef : null}>
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
          fmtId === 'brief'
            ? 'What you see here is what prints, caveats included, so nothing reaches a reader ' +
              'that you have not read first. It is held to a single page: every finding and ' +
              'every reading is here, and the evidence under them is trimmed to the first few ' +
              'rows, with each trimmed figure saying so. The deck carries the explanatory ' +
              'sentences and more of the rows.'
            : 'What you see here is what prints, caveats included. One slide per finding, and ' +
              'a closing slide carrying the rules the figures rest on.'
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
