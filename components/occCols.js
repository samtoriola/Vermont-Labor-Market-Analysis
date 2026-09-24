'use client';

import { fmt, money } from '@/lib/format';

/**
 * Column spec for occupation tables, shared by the master view and the drill-down
 * so both carry the same measures and export the same shape.
 *
 * `get` returns the underlying value; DataTable renders and sorts from that, which
 * is why sorting by Median behaves numerically rather than alphabetically.
 */
export function occCols(lwAnnual) {
  return [
    { k: 'n', label: 'Occupation', kind: 'text', get: (o) => o.n },
    { k: 'j', label: 'Jobs 2025', kind: 'num', get: (o) => o.j },
    { k: 'chgPct', label: 'Change 2021–25', kind: 'pct', get: (o) => o.chgPct },
    { k: 'g', label: 'Projected 25–30', kind: 'pct', get: (o) => o.g },
    { k: 'm', label: 'Median', kind: 'money', get: (o) => o.m },
    { k: 'lw', label: 'vs living wage', kind: 'x', get: (o) => (o.m ? o.m / lwAnnual : null) },
    { k: 'o', label: 'Openings /yr', kind: 'num', get: (o) => o.o },
    { k: 'turn', label: 'Turnover', kind: 'rate', get: (o) => o.turn },
    { k: 'pp', label: 'Postings /100', kind: 'num1', get: (o) => (o.j ? (o.p / o.j) * 100 : null) },
    { k: 't', label: 'Entry credential', kind: 'text', get: (o) => o.t },
  ];
}

/** Master table also names the family and SOC, which the drill-down already implies. */
export function occColsWide(lwAnnual) {
  return occCols(lwAnnual).concat([
    { k: 'f', label: 'Family', kind: 'text', get: (o) => o.f },
    { k: 's', label: 'SOC', kind: 'text', get: (o) => o.s },
  ]);
}

/**
 * Tooltip for a single occupation dot. Reference columns come from OEWS and carry
 * a percentile range but none of the Vermont-only Lightcast fields, so those rows
 * are only added when they exist.
 */
export function occDotTip(lwAnnual) {
  return (d, g) => ({
    title: d.n,
    rows: [
      ['Median pay', money(d.v)],
      ['Jobs', fmt(d.e)],
      ...(d.lo ? [['10th to 90th', money(d.lo) + ' to ' + money(d.hi)]] : []),
      ...(g && g.ref
        ? []
        : [
            ['vs living wage', (d.v / lwAnnual).toFixed(2) + '×'],
            [
              'Projected 2025-30',
              d.g === null || d.g === undefined ? '—' : (d.g >= 0 ? '+' : '') + d.g + '%',
            ],
            [
              'Turnover',
              d.turn === null || d.turn === undefined ? '—' : d.turn.toFixed(1) + '%',
            ],
            ['Entry credential', d.t || '—'],
          ]),
    ],
  });
}

/** Tooltip for a single ACS respondent dot. */
export function personTip(lwAnnual) {
  return (d) => ({
    title: 'One ACS respondent',
    rows: [
      ['Earnings, 2024', money(d.v)],
      ['vs living wage', (d.v / lwAnnual).toFixed(2) + '×'],
      ['Age', String(d.a)],
      ['Usual hours a week', String(d.h)],
      ['Occupation group', d.f || '—'],
    ],
  });
}
