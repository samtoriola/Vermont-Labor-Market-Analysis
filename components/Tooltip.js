'use client';

import { createContext, useContext, useState, useCallback, useRef } from 'react';

const TipContext = createContext({ show: () => {}, hide: () => {} });

export function useTip() {
  return useContext(TipContext);
}

/**
 * Hover/focus tooltip shared by every chart.
 *
 * show(event, title, rows, meta) where rows is an array of [label, value] pairs and
 * meta is optional: { sub, big: [[value, note]], foot }.
 *
 * `big` is the card's headline -- the measure the mark is, set large with a line of
 * plain English under it, rather than as one more row in a list where it reads as no
 * more important than the turnover rate. `foot` says what a click does, which is the
 * only way a reader learns a bar is clickable before clicking it.
 */
export function TooltipProvider({ children }) {
  const [tip, setTip] = useState(null);
  const raf = useRef(0);

  const show = useCallback((e, title, rows, meta) => {
    const cx = e.clientX;
    const cy = e.clientY;
    cancelAnimationFrame(raf.current);
    raf.current = requestAnimationFrame(() => {
      setTip({ title, rows: rows || [], meta: meta || {}, cx, cy });
    });
  }, []);

  const hide = useCallback(() => {
    cancelAnimationFrame(raf.current);
    setTip(null);
  }, []);

  const meta = tip ? tip.meta : {};
  const big = meta.big || [];

  let style = { opacity: 0 };
  if (tip) {
    const pad = 14;
    const w = 272;
    // Rough, and only used to decide which side of the cursor the card sits on.
    const h =
      30 + (meta.sub ? 16 : 0) + big.length * 40 + tip.rows.length * 19 + (meta.foot ? 24 : 0);
    let x = tip.cx + pad;
    let y = tip.cy + pad;
    if (typeof window !== 'undefined') {
      if (x + w > window.innerWidth) x = tip.cx - w - pad;
      if (y + h > window.innerHeight) y = tip.cy - h - 4;
    }
    style = { opacity: 1, left: Math.max(6, x) + 'px', top: Math.max(6, y) + 'px' };
  }

  return (
    <TipContext.Provider value={{ show, hide }}>
      {children}
      <div id="tip" role="status" aria-live="polite" style={style}>
        {tip ? (
          <>
            <div className="tt">{tip.title}</div>
            {meta.sub ? <div className="tsub">{meta.sub}</div> : null}
            {big.map((b, i) => (
              <div className="tbig" key={i}>
                <div className="bv">{b[0]}</div>
                {b[1] ? <div className="bn">{b[1]}</div> : null}
              </div>
            ))}
            {tip.rows.length ? (
              <div className={big.length ? 'trows ruled' : 'trows'}>
                {tip.rows.map((r, i) => (
                  <div className="tr" key={i}>
                    <span>{r[0]}</span>
                    <b>{r[1]}</b>
                  </div>
                ))}
              </div>
            ) : null}
            {meta.foot ? <div className="tfoot">{meta.foot}</div> : null}
          </>
        ) : null}
      </div>
    </TipContext.Provider>
  );
}

/**
 * Wraps an SVG mark so it responds to hover and keyboard focus identically.
 * Spread the result onto an <g>, <rect> or <circle>.
 */
export function useTipHandlers(title, rows, meta) {
  const { show, hide } = useTip();
  return {
    tabIndex: 0,
    onMouseMove: (e) => show(e, title, rows, meta),
    onMouseLeave: hide,
    onFocus: (e) => {
      const b = e.currentTarget.getBoundingClientRect();
      show({ clientX: b.left + b.width / 2, clientY: b.top + b.height }, title, rows, meta);
    },
    onBlur: hide,
  };
}
