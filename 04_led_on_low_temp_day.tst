# 04_led_on_low_temp_day.tst
# Purpose: On a cold day during daytime, LEDs should raise temperature toward optimal lower bound.
# Expected: LED ON ≤ 60s; reach optimal lower temp within 20m or keep LEDs on while cold.

BASELINE = /home/robotanist/TerraBot/param/low_temp_baseline.bsl
DELAY FOR 60

WHENEVER enabled("RaiseTempBehavior") and temperature <= limits['temperature'][0] and (mtime//3600) >= 6 and (mtime//3600) < 22 WHILE enabled("RaiseTempBehavior")
  WAIT led FOR 60
  ENSURE led or temperature >= optimal['temperature'][0] FOR 1200
  PRINT "led: %s; temperature: %d (warming…)" %(led, temperature)

QUIT AT 1-23:59:59