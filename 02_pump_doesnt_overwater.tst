# 02_pump_doesnt_overwater.tst
# Purpose: When soil starts very dry, pump may engage, but moisture must not overshoot unsafe levels.
# Expected: Pump turns ON ≤ 10 min; while ON, smoist < 700 for 1h.

BASELINE = dry_soil.bsl
DELAY FOR 60

# Safety: do not overwater while pumping
WHENEVER wpump
  ENSURE smoist < 700 FOR 3600

QUIT AT 1-23:59:59