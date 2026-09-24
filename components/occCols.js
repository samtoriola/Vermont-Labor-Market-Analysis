'use client';

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
