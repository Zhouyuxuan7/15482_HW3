# 06_dehumidify_progress_then_opt.tst
# Purpose: With high RH, controller should produce measurable progress, then reach optimal upper bound.
# Expected: After 15m settle, drop ≥ 2 within 3h; reach optimal upper ≤ 8h.

BASELINE = /home/robotanist/TerraBot/param/high_humid_baseline.bsl
DELAY FOR 60

WHENEVER humidity >= limits['humidity'][1]
  PRINT "High RH %s RH=%d upper=%d" %(clock_time(time), humidity, limits['humidity'][1])
  WAIT FOR 900
  SET h0 = humidity
  WAIT (h0 - humidity) >= 2 FOR 10800
  WAIT humidity <= optimal['humidity'][1] FOR 28800
  SET hdrop = (h0 - humidity)
  PRINT "Dehumidify OK %s drop=%d final=%d target<=%d" %(clock_time(time), hdrop, humidity, optimal['humidity'][1])

QUIT AT 2-00:00:00