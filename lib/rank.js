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

  // Floor, not ceiling: on an odd count the spare row goes to the bottom slice.
  // The top slice is the one that gets exported and put on a slide, and "Top 10"
  // is a view someone will present where "Top 11" invites the question of what
  // the eleventh is doing there. Nobody presents the bottom half, so that is
  // where the awkward number belongs.
  const top = Math.floor(n / 2);
  return [
    { id: 'all', label: `All ${n}`, n },
    { id: 'top', label: `Top ${top}`, n: top },
    { id: 'bottom', label: `Bottom ${n - top}`, n: n - top },
  ];
}

/** The default view: the one the chart had before it gained a control. */
export function defaultView(show) {
  return show ? 'top' : 'all';
}

export function applyView(rows, view, show) {
  if (!rows || !rows.length) return rows;
  const n = rows.length;
  const top = show && show < n ? show : Math.floor(n / 2);
  if (view === 'top') return rows.slice(0, top);
  // Where the pool splits in half, the bottom is whatever the top leaves, which
  // on an odd count is one row more -- the halves have to partition the pool,
  // not share a row between them. Where `show` is set the two views are both
  // that size by definition and cannot overlap.
  const size = show && show < n ? show : n - top;
  if (view === 'bottom') {
    // Reversed, so the bottom of the ranking is the top of the chart.
    return rows.slice(Math.max(0, n - size)).reverse();
  }
  return rows;
}
