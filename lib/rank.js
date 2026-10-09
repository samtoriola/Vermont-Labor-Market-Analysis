/**
 * Top / bottom views of a ranked chart.
 *
 * A ranked chart with twenty-odd rows runs past 800px, which reads fine in a
 * browser and not at all on a slide. Rather than cut the data to fit, every long
 * ranked chart offers the same three views of the same rows, so what gets left
 * out is the reader's choice and is stated on the control.
 *
 * Which rows are taken comes from the order the chart was given, so "bottom" is
 * the end of the ranking the reader is already looking at. The bottom slice is
 * then reversed, so each view opens on its own extreme: a top view leads with the
 * largest, a bottom view with the smallest. Reading either one, the first bar is
 * the one the view exists to show.
 */

/* Beyond this a chart is too tall to be worth offering whole. */
const ALL_MAX = 45;

/**
 * The views available for a list of `n` rows.
 *
 * `show` is how many the chart displays by default. Where it is set the chart is
 * already a top slice of a longer pool, so the choice is between the two ends of
 * that pool at the size the chart was built for. Where it is not, the chart shows
 * a complete population, and the halves are what make it fit.
 *
 * Returns [] when there is nothing worth choosing between.
 */
export function rankViews(n, show) {
  if (!n || n < 14) return [];

  if (show && show < n) {
    const views = [
      { id: 'top', label: `Top ${show}`, n: show },
      { id: 'bottom', label: `Bottom ${show}`, n: show },
    ];
    if (n <= ALL_MAX) views.push({ id: 'all', label: `All ${n}`, n });
    return views;
  }

  const half = Math.ceil(n / 2);
  return [
    { id: 'all', label: `All ${n}`, n },
    { id: 'top', label: `Top ${half}`, n: half },
    { id: 'bottom', label: `Bottom ${n - half}`, n: n - half },
  ];
}

/** The default view: the one the chart had before it gained a control. */
export function defaultView(show) {
  return show ? 'top' : 'all';
}

export function applyView(rows, view, show) {
  if (!rows || !rows.length) return rows;
  const n = rows.length;
  const size = show && show < n ? show : Math.ceil(n / 2);
  if (view === 'top') return rows.slice(0, size);
  // Reversed, so the bottom of the ranking is the top of the chart.
  if (view === 'bottom') return rows.slice(Math.max(0, n - size)).reverse();
  return rows;
}
