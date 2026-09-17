"""Turn the BigQuery county GeoJSON into compact SVG paths for the Vermont map.

Equal-aspect projection (lon scaled by cos(mean lat)) fitted to a viewBox, then
Douglas-Peucker simplification. Rings smaller than a threshold are dropped, except
where a county IS islands (Grand Isle), so its shape survives.
"""
import json, math, pathlib

RAW = json.loads(pathlib.Path("vt_counties_raw.json").read_text(encoding="utf-8"))
W, H = 300.0, 460.0          # viewBox; Vermont is tall and narrow
PAD = 6.0
TOL = 0.0018                 # simplification tolerance in projected units
MIN_RING_AREA = 0.00004      # drop slivers

NAMES = {r["county_fips_code"]: r["county_name"] for r in RAW}

def rings_of(geom):
    t = geom["type"]
    if t == "Polygon":
        return [geom["coordinates"][0]]
    if t == "MultiPolygon":
        return [poly[0] for poly in geom["coordinates"]]
    raise ValueError(t)

# ---- collect, find bounds ----
county_rings = {}
lons, lats = [], []
for r in RAW:
    g = json.loads(r["gj"])
    rs = rings_of(g)
    county_rings[r["county_fips_code"]] = rs
    for ring in rs:
        for lon, lat in ring:
            lons.append(lon); lats.append(lat)

lon0, lon1 = min(lons), max(lons)
lat0, lat1 = min(lats), max(lats)
latm = math.radians((lat0 + lat1) / 2)
kx = math.cos(latm)
print(f"bounds lon {lon0:.4f}..{lon1:.4f}  lat {lat0:.4f}..{lat1:.4f}  cos(lat)={kx:.4f}")

def proj(lon, lat):
    return ((lon - lon0) * kx, (lat1 - lat))

px0 = py0 = 0.0
px1 = (lon1 - lon0) * kx
py1 = (lat1 - lat0)
sx = (W - 2 * PAD) / px1
sy = (H - 2 * PAD) / py1
s = min(sx, sy)                      # uniform scale: no distortion
offx = PAD + ((W - 2 * PAD) - px1 * s) / 2
offy = PAD + ((H - 2 * PAD) - py1 * s) / 2
print(f"scale={s:.2f}  drawn size {px1*s:.1f} x {py1*s:.1f}")

def to_xy(lon, lat):
    x, y = proj(lon, lat)
    return (offx + x * s, offy + y * s)

# ---- Douglas-Peucker ----
def dp(pts, tol):
    if len(pts) < 3:
        return pts
    def seg_dist(p, a, b):
        (px, py), (ax, ay), (bx, by) = p, a, b
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        worst, wi = -1, i
        for k in range(i + 1, j):
            d = seg_dist(pts[k], pts[i], pts[j])
            if d > worst:
                worst, wi = d, k
        if worst > tol:
            keep[wi] = True
            stack += [(i, wi), (wi, j)]
    return [p for p, k in zip(pts, keep) if k]

def ring_area(ring):
    a = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2

out, raw_pts, kept_pts = {}, 0, 0
for fips, rs in county_rings.items():
    # Relative threshold: keep any ring at least 6% of this county's largest.
    # An absolute cut-off erased Grand Isle's island chain.
    allp = [[proj(lon, lat) for lon, lat in ring] for ring in rs]
    biggest = max(ring_area(p) for p in allp)
    projected = [p for p in allp if ring_area(p) >= max(biggest * 0.06, MIN_RING_AREA * 0.05)]
    if not projected:
        projected = [max(allp, key=ring_area)]
    paths = []
    for pr in projected:
        raw_pts += len(pr)
        simp = dp(pr, TOL)
        if len(simp) < 4:
            continue
        kept_pts += len(simp)
        pts = [(offx + x * s, offy + y * s) for x, y in simp]
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
        paths.append(d)
    out[fips] = {"n": NAMES[fips].replace(" County", ""), "d": " ".join(paths),
                 "rings": len(paths)}

print(f"points {raw_pts:,} -> {kept_pts:,}  ({kept_pts/raw_pts*100:.1f}%)")
for f in sorted(out):
    print(f"  {f} {out[f]['n']:12s} rings={out[f]['rings']}  {len(out[f]['d']):5d} chars")

payload = {"viewBox": f"0 0 {int(W)} {int(H)}", "counties": out}
js = json.dumps(payload, separators=(",", ":"))
pathlib.Path("vt_map.json").write_text(js, encoding="utf-8")
print(f"\nvt_map.json: {len(js):,} bytes")
