# 07_wet_soil_evap_no_pump.tst
# Purpose: Starting from wet soil, system must not pump and should slowly dry via evaporation (allowing noise).
# Expected: No pump for 4h; no net increase beyond +2 noise; drop ≥ 5 within 12h.

BASELINE = soggy_soil.bsl
DELAY FOR 60

WHENEVER smoist >= limits['moisture'][1]
  PRINT "Wet soil %s smoist=%d upper=%d" %(clock_time(time), smoist, limits['moisture'][1])
  SET m0 = smoist
  ENSURE not wpump FOR 14400
  ENSURE smoist <= (m0 + 2) FOR 14400
  WAIT (m0 - smoist) >= 5 FOR 43200
  SET mdone = (m0 - smoist)
  PRINT "Drying OK %s delta=%d final=%d upper=%d" %(clock_time(time), mdone, smoist, limits['moisture'][1])

QUIT AT 2-00:00:00