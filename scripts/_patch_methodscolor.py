"""Methods' Color panel owes the scatter an exception.

The panel's swatches say green is "at or above living wage", and on the Wage
quality scatter that half is Ocean. A register that does not match the screen is
worse than no register, so the rule states the exception and the reason for it.
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
H = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(H, "..", "components", "views", "Methods.js")
s = io.open(P, encoding="utf-8").read()

old = """          86% red reads as an alarm rather than a measurement, which is why Wage quality and the
          Overview use the ordinal ramp instead.
        </p>"""
new = """          86% red reads as an alarm rather than a measurement, which is why Wage quality and the
          Overview use the ordinal ramp instead. Where the two sides are points rather than a
          range — the scatter of every occupation on Wage quality — the shortfall keeps red
          and the other half takes Ocean rather than green. Green against red is too close to
          tell apart under the commonest colour blindness, and a point carries no value label
          to read instead; the benchmark line separates the two either way.
        </p>"""

if s.count(old) != 1:
    raise SystemExit("%d occurrences" % s.count(old))
io.open(P, "w", encoding="utf-8", newline="").write(s.replace(old, new))
print("Methods.js patched")
