# 01_fan_cools_hotstart.tst
# Purpose: From a hot start at night, the fan should engage and produce measurable cooling.
# Expected: Fan ON ≤ 10 min; temp drop ≥ 1C within 3h. Fails if fan never engages or no cooling observed.
# Robust to startup: only asserts once LowerTempBehavior is enabled.

BASELINE = night_hot.bsl
DELAY FOR 30

WHENEVER enabled("LowerTempBehavior") and (temperature >= 32) WHILE enabled("LowerTempBehavior")
  PRINT "Hot start at %s temp=%d fan=%s (behavior enabled)" %(clock_time(time), temperature, fan)

  WAIT FOR 120

  # Fan should turn on within 10 minutes of this point
  WAIT fan FOR 600

  # Then require measurable cooling within 3 hours
  SET t0 = temperature
  WAIT (t0 - temperature) >= 1 FOR 10800
  PRINT "Cooling observed by %s start=%d now=%d" %(clock_time(time), t0, temperature)

QUIT AT 2-00:00:00