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
