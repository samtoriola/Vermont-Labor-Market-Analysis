'use client';

import { createContext, useContext, useState, useCallback, useRef } from 'react';

const TipContext = createContext({ show: () => {}, hide: () => {} });

export function useTip() {
  return useContext(TipContext);
}

/**
 * Hover/focus tooltip shared by every chart. Charts call show(event, title, rows)
 * where rows is an array of [label, value] pairs.
 */
export function TooltipProvider({ children }) {
  const [tip, setTip] = useState(null);
  const raf = useRef(0);

  const show = useCallback((e, title, rows) => {
    const cx = e.clientX;
    const cy = e.clientY;
    cancelAnimationFrame(raf.current);
    raf.current = requestAnimationFrame(() => {
      setTip({ title, rows: rows || [], cx, cy });
    });
  }, []);

  const hide = useCallback(() => {
    cancelAnimationFrame(raf.current);
    setTip(null);
  }, []);

  let style = { opacity: 0 };
  if (tip) {
    const pad = 14;
    const w = 268;
    const h = 34 + tip.rows.length * 19;
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
            {tip.rows.map((r, i) => (
              <div className="tr" key={i}>
                <span>{r[0]}</span>
                <b>{r[1]}</b>
              </div>
            ))}
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
export function useTipHandlers(title, rows) {
  const { show, hide } = useTip();
  return {
    tabIndex: 0,
    onMouseMove: (e) => show(e, title, rows),
    onMouseLeave: hide,
    onFocus: (e) => {
      const b = e.currentTarget.getBoundingClientRect();
      show({ clientX: b.left + b.width / 2, clientY: b.top + b.height }, title, rows);
    },
    onBlur: hide,
  };
}
