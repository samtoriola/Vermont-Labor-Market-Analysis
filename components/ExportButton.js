'use client';

import { downloadCsv, exportName } from '@/lib/csv';

/* Its own module so both ui.js and DataTable.js can use it: ui.js renders the
   tables DataTable draws, and DataTable puts this button on them, which would
   otherwise be an import cycle between the two. */
/** Downloads the panel's underlying rows as CSV. Client-side; nothing is uploaded. */
export function ExportButton({ label, cols, rows }) {
  if (!rows || !rows.length) return null;
  return (
    <button
      type="button"
      className="exportbtn"
      onClick={() => downloadCsv(exportName(label), cols, rows)}
      title={`Download ${rows.length} rows as CSV`}
    >
      Export CSV
    </button>
  );
}
