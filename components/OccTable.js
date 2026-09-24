'use client';

import { LC, lwAnnual, occByFamily } from '@/lib/data';
import { fmt } from '@/lib/format';
import { useFilters } from './FilterContext';
import { useDrill, occDrill } from './Drill';
import DataTable from './DataTable';
import { occColsWide } from './occCols';

/**
 * The master occupation table. Responds to the shared cross-filters, and adds its
 * own search / column filter / sort on top via DataTable.
 *
 * Observed change (2021-2025) sits next to the projection (2025-2030) deliberately:
 * the two disagree, and showing only the forecast invites reading it as history.
 */
export default function OccTable({ lw }) {
  const { apply } = useFilters();
  const { open } = useDrill();
  const LWA = lwAnnual(lw);
  const rows = apply(LC.allOcc);

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>All occupations</h3>
      </div>
      <p className="cap">
        Every Vermont occupation passing the filters above. Search, filter on any numeric
        column, or click a heading to sort — then export exactly what you are looking at.
        Click a row to open its occupational family.
      </p>

      <DataTable
        cols={occColsWide(LWA)}
        rows={rows}
        initialSort={{ k: 'j', dir: -1 }}
        exportLabel="all-occupations"
        rowKey={(r) => r.s}
        onRowClick={(r) =>
          open(
            occDrill({
              label: 'Occupational family',
              title: r.f,
              cap: `Opened from ${r.n}. Every occupation in this family.`,
              occ: occByFamily(r.f),
              lwAnnual: LWA,
            })
          )
        }
      />

      <div className="srcline">
        Lightcast · observed change from 2021/2025 jobs · projection from 2030 jobs ·
        turnover is separations ÷ jobs and counts job-to-job transfers, so it reads as
        churn rather than unmet demand · suppressed below 10 jobs
      </div>
    </div>
  );
}
