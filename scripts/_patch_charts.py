"""Splices RangeRows into components/charts.js. Throwaway."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "components", "charts.js")
s = io.open(P, encoding="utf-8").read()
block = io.open(os.path.join(H, "_rangerows.jsx"), encoding="utf-8").read()

ANCHOR = """/* ------------------------------------------------------------------ *
 * 100% stacked rows"""
assert s.count(ANCHOR) == 1, s.count(ANCHOR)
assert "RangeRows" not in s, "already patched"
s = s.replace(ANCHOR, block + ANCHOR)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("charts.js patched,", len(s), "bytes")
