/**
 * The coordinate width every chart is drawn in.
 *
 * Charts are authored in a fixed viewBox and rendered at `width: 100%`, so the
 * browser scales the whole drawing -- labels included -- by the panel width over
 * this number. At 860 a chart in a wide panel was scaled about 1.6x, which put its
 * axis and column labels at 15-19px: larger than any text in the interface around
 * them. Drawing in a wider coordinate space leaves the scale near 1, so chart text
 * lands at the size it was authored at and sits with the rest of the page.
 *
 * Geometry in both chart modules is derived from this, so changing it moves the
 * drawing without moving the type.
 */
export const CHART_W = 1180;

/**
 * The same, for a chart that has given part of its panel to a detail pane.
 *
 * The pane is a fixed 420px, so the chart keeps whatever is left of the panel. Drawn
 * in a narrower coordinate space it scales back up to about the same factor it had
 * at full width, which is why the labels do not shrink when a bar is clicked.
 */
export const SPLIT_W = 1040;
