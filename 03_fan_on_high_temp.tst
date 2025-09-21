# 03_fan_on_high_temp.tst
# Purpose: If LowerTempBehavior is enabled and temp ≥ upper limit, fan engages quickly and cools toward optimal.
# Expected: Fan ON ≤ 60s; either fan stays on or temperature ≤ optimal upper within 30m.

BASELINE = /home/robotanist/TerraBot/param/high_temp_baseline.bsl
DELAY FOR 60

WHENEVER enabled("LowerTempBehavior") and temperature >= limits['temperature'][1] WHILE enabled("LowerTempBehavior")
  WAIT fan FOR 60
  ENSURE fan or temperature <= optimal['temperature'][1] FOR 1800
  PRINT "fan: %s; temperature: %d; cool-to: %d" %(fan, temperature, optimal['temperature'][1])

QUIT AT 1-23:59:59