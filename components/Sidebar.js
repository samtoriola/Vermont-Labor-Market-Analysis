'use client';

import { NAV } from '@/lib/nav';

/**
 * Persistent left navigation. Group headings are labels, not controls -- a group has
 * no page of its own, so making it clickable would promise something that is not there.
 * Every destination in the dashboard is reachable from here without opening anything.
 */
export default function Sidebar({ view, section, onGo, collapsed, onToggle }) {
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
              <div className="sbgroup" key={n.view}>
                <div className="sbhead">{n.label}</div>
                {n.items.map((it) => {
                  const on = view === n.view && section === it.id;
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
                })}
              </div>
            )
          )}
        </div>
      )}
    </nav>
  );
}
