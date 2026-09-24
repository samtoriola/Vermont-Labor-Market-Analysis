/** CSV export. Client-side only — no server round trip, nothing leaves the browser. */

function esc(v) {
  if (v === null || v === undefined) return '';
  const s = String(v);
  // Strip the display formatting so the CSV carries values a spreadsheet can use:
  // $53,886 -> 53886, 12.4% -> 12.4, 1.38× -> 1.38, em-dash -> empty.
  const cleaned = s
    .replace(/—/g, '')
    .replace(/[$,]/g, '')
    .replace(/[%×]/g, '')
    .trim();
  const out = cleaned !== '' && !Number.isNaN(Number(cleaned)) ? cleaned : s;
  return /[",\n]/.test(out) ? '"' + out.replace(/"/g, '""') + '"' : out;
}

export function toCsv(cols, rows) {
  const head = cols.map(esc).join(',');
  const body = rows.map((r) => (r.cells || r).map(esc).join(',')).join('\n');
  return head + '\n' + body + '\n';
}

/**
 * Trigger a download. Guarded: if the browser blocks object URLs the export is a
 * no-op rather than an exception, because a failed download should not break the page.
 */
export function downloadCsv(filename, cols, rows) {
  try {
    const blob = new Blob([toCsv(cols, rows)], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename.endsWith('.csv') ? filename : filename + '.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 0);
    return true;
  } catch (e) {
    return false;
  }
}

/** Filename-safe slug, prefixed so exports group together in a downloads folder. */
export function exportName(label) {
  const slug = String(label)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 60);
  return `vt-labor-${slug}`;
}
