// Strada brand palette, Brand Guide 2025. Do not retype these elsewhere.
//
// The guide applies the palette unequally: Midnight is text, Ocean and Pine are
// the workhorses for larger fields, and Vine / Ember / Sky are accents only.
// Mist is the neutral.
export const BRAND = {
  midnight: '#1C252D',
  sky: '#00FFFB',
  ocean: '#009BA5',
  vine: '#4FCB00',
  pine: '#007A58',
  ember: '#FC4C3A',
  mist: '#CED2D5',
};

// Categorical series order, capped at four.
//
// Validated with the dataviz palette checker (light surface): lightness band PASS,
// chroma floor PASS, adjacent CVD worst 6.7 ΔE (Vine↔Ember, deutan) which sits in
// the 6–8 band and is legal only with secondary encoding — every chart here carries
// direct value labels, which satisfies it. Vine's contrast vs surface is 2.07:1, so
// it also relies on those labels.
//
// Reordering breaks this: Ocean, Ember, Pine, Vine FAILS at 4.5 ΔE (Pine↔Ember).
// Midnight and Mist are excluded from series use — both fail the lightness band and
// the chroma floor, i.e. they read as grey, which is why the guide reserves them.
export const SERIES = ['--s1', '--s2', '--s3', '--s4'];
export const SERIES_HEX = [BRAND.ocean, BRAND.ember, BRAND.vine, BRAND.pine];

// Ordinal / sequential ramp: one hue, light to dark, from the Ocean tints.
// Used for the credential ladder (which is ordered, not categorical) and the map.
export const ORDINAL = ['--ord1', '--ord2', '--ord3', '--ord4', '--ord5'];
export const ORDINAL_HEX = ['#CCEBED', '#99D7DB', '#66C3C9', '#33AFB7', '#009BA5'];

// Semantic pair, reserved. Never reused as a series colour.
export const GOOD = '--good'; // Pine  — at or above the benchmark
export const BAD = '--bad';   // Ember — below the benchmark
export const GOOD_HEX = BRAND.pine;
export const BAD_HEX = BRAND.ember;

/** Pick an ordinal ramp step for a 0..1 position. */
export function rampStep(t) {
  const i = Math.min(ORDINAL.length - 1, Math.max(0, Math.floor(t * ORDINAL.length)));
  return ORDINAL[i];
}

export function rampHex(t) {
  const i = Math.min(ORDINAL_HEX.length - 1, Math.max(0, Math.floor(t * ORDINAL_HEX.length)));
  return ORDINAL_HEX[i];
}
