'use client';

import { useState, useEffect, useCallback } from 'react';
import { NAV } from '@/lib/nav';

const KEY = 'vt-closed';

/**
 * Persistent left navigation. Each topic collapses, and which ones are closed is
 * remembered. The group holding the open section is always shown expanded whatever
 * was stored, so the sidebar can never hide where the reader currently is.
 */
export default function Sidebar({ view, section, onGo, collapsed, onToggle }) {
  const [closed, setClosed] = useState([]);

  useEffect(() => {
    try {
      const v = localStorage.getItem(KEY);
      if (v) setClosed(v.split(',').filter(Boolean));
    } catch (e) {
      /* blocked storage — everything stays open */
    }
  }, []);

  const toggleGroup = useCallback((id) => {
    setClosed((cur) => {
      const next = cur.includes(id) ? cur.filter((x) => x !== id) : cur.concat(id);
      try {
        localStorage.setItem(KEY, next.join(','));
      } catch (e) {
        /* non-fatal */
      }
      return next;
    });
  }, []);

  return (
    <nav className={collapsed ? 'sidebar collapsed' : 'sidebar'} aria-label="Sections">
      <button
        type="button"
        className="sbtoggle"
        onClick={onToggle}
        aria-expanded={!collapsed}
        title={collapsed ? 'Expand navigation' : 'Collapse navigation'}
      >
        <span aria-hidden="true">{collapsed ? '»' : '«'}</span>
        <span className="vh">{collapsed ? 'Expand navigation' : 'Collapse navigation'}</span>
      </button>

      {collapsed ? null : (
        <div className="sbin">
          {NAV.map((n) =>
            n.kind === 'item' ? (
              <button
                key={n.view}
                type="button"
                className={'sbitem top' + (view === n.view ? ' on' : '')}
                aria-current={view === n.view ? 'page' : undefined}
                onClick={() => onGo(n.view, null)}
              >
                {n.label}
              </button>
            ) : (
              (() => {
                // Never collapse the topic the reader is currently inside.
                const here = view === n.view;
                const isOpen = here || !closed.includes(n.view);
                return (
                  <div className="sbgroup" key={n.view}>
                    <button
                      type="button"
                      className="sbhead"
                      aria-expanded={isOpen}
                      onClick={() => toggleGroup(n.view)}
                    >
                      <span className={isOpen ? 'chev open' : 'chev'} aria-hidden="true">
                        {'›'}
                      </span>
                      {n.label}
                    </button>
                    {isOpen
                      ? n.items.map((it) => {
                          const on = here && section === it.id;
                          return (
                            <button
                              key={it.id}
                              type="button"
                              className={'sbitem' + (on ? ' on' : '')}
                              aria-current={on ? 'page' : undefined}
                              onClick={() => onGo(n.view, it.id)}
                            >
                              {it.label}
                            </button>
                          );
                        })
                      : null}
                  </div>
                );
              })()
            )
          )}
        </div>
      )}
    </nav>
  );
}
