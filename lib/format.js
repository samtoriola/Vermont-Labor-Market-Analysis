export function fmt(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return Math.round(n).toLocaleString('en-US');
}

export function money(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return '$' + Math.round(n).toLocaleString('en-US');
}

export function pct(n, d = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return (n * 100).toFixed(d) + '%';
}

export function niceMax(v) {
  if (!v || v <= 0) return 1;
  const mag = Math.pow(10, Math.floor(Math.log10(v)));
  const steps = [1, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10];
  for (const s of steps) if (s * mag >= v) return s * mag;
  return 10 * mag;
}

export function trunc(s, n) {
  const str = String(s);
  return str.length > n ? str.slice(0, n - 1) + '…' : str;
}

// Value formatter shared by the chart axes and data labels.
export function fmtVal(v, o = {}) {
  if (o.money) return money(v);
  if (o.mode === 'pct') {
    const d = o.dec === undefined ? 1 : o.dec;
    return (o.signed && v > 0 ? '+' : '') + v.toFixed(d) + '%';
  }
  if (o.dec !== undefined) return v.toFixed(o.dec);
  return fmt(v);
}
