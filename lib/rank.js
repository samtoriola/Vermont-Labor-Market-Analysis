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
 * How many rows the top slice takes.
 *
 * Not half. Half of 22 is 11, and "Top 11" invites the question of what the
 * eleventh is doing there -- the top slice is the one that gets exported and put
 * in front of people, so it should be a number someone would choose to present.
 * Where half the pool is ten or more the slice rounds down to a multiple of ten
 * and the bottom takes whatever is left, which is why 22 occupation groups split
 * 10 and 12 rather than 11 and 11.
 *
 * Below ten there is no round number to reach for and rounding down would throw
 * most of the chart away, so a small pool just splits. The two slices always
 * partition the pool; they never share a row.
 */
function topSlice(n) {
  const half = Math.floor(n / 2);
  return half >= 10 ? Math.floor(half / 10) * 10 : half;
}

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

  const top = topSlice(n);
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
  const top = show && show < n ? show : topSlice(n);
  if (view === 'top') return rows.slice(0, top);
  // Where the pool splits, the bottom is whatever the top leaves -- which is
  // more than half, because topSlice rounds the top down to a round number. The
  // two have to partition the pool, not share a row between them. Where `show`
  // is set both views are that size by definition and cannot overlap.
  const size = show && show < n ? show : n - top;
  if (view === 'bottom') {
    // Reversed, so the bottom of the ranking is the top of the chart.
    return rows.slice(Math.max(0, n - size)).reverse();
  }
  return rows;
}
