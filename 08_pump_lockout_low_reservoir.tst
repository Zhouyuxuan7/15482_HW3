# 08_pump_lockout_low_reservoir.tst
# Purpose: With low reservoir (below safe), pump must never run.
# Expected: No pump for at least 2h while below safe level.

BASELINE = low_water_level.bsl
DELAY FOR 60

WHENEVER wlevel <= limits['water_level'][0]
  ENSURE not wpump FOR 7200
  PRINT "Reservoir low (wlevel=%d). Pump lockout active." %wlevel

QUIT AT 1-23:59:59