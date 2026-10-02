'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * Vertical sub-navigation inside a tab. Each item is one topic, and only the active
 * one is built -- `render` is a function rather than a node so a chart with a few
 * thousand marks is never constructed for a section nobody is looking at.
 *
 * items: { id, label, render: () => node }
 */
export default function Sections({ id, items }) {
  const first = items.length ? items[0].id : null;
  const [active, setActive] = useState(first);
  const key = `vt-sec-${id}`;

  // Restore after mount so the server and first client render agree.
  useEffect(() => {
    try {
      const v = localStorage.getItem(key);
      if (v && items.some((x) => x.id === v)) setActive(v);
    } catch (e) {
      /* blocked storage — keep the default */
    }
    // items is derived from the data, so its identity changes every render; the id
    // list is what actually matters here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, items.map((x) => x.id).join('|')]);

  // A filter can remove the section that was open, so fall back to the first.
  const current = items.some((x) => x.id === active) ? active : first;

  const select = useCallback(
    (next) => {
      setActive(next);
      try {
        localStorage.setItem(key, next);
      } catch (e) {
        /* non-fatal */
      }
    },
    [key]
  );

  // Arrow keys move between sections, which is what a vertical tablist should do.
  const onKey = (e, i) => {
    const d = e.key === 'ArrowDown' ? 1 : e.key === 'ArrowUp' ? -1 : 0;
    if (!d) return;
    e.preventDefault();
    const next = items[(i + d + items.length) % items.length];
    select(next.id);
    const el = document.getElementById(`sec-${id}-${next.id}`);
    if (el) el.focus();
  };

  if (!items.length) return null;
  const shown = items.filter((x) => x.id === current)[0];

  return (
    <div className="sections">
      <nav className="subnav" role="tablist" aria-orientation="vertical" aria-label="Topics">
        {items.map((it, i) => (
          <button
            key={it.id}
            id={`sec-${id}-${it.id}`}
            type="button"
            role="tab"
            aria-selected={it.id === current}
            aria-controls={`secpanel-${id}`}
            tabIndex={it.id === current ? 0 : -1}
            onClick={() => select(it.id)}
            onKeyDown={(e) => onKey(e, i)}
          >
            {it.label}
          </button>
        ))}
      </nav>
      <div
        className="secbody"
        id={`secpanel-${id}`}
        role="tabpanel"
        aria-labelledby={`sec-${id}-${current}`}
      >
        {shown.render()}
      </div>
    </div>
  );
}
