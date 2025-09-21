# 05_night_light_policy.tst
# Purpose: Verify LED night cycle — ON at night, OFF in morning.
# Trigger at 22:00 day 1, give a grace period, require LED ON & held; 
# then at 06:00 day 2 require LED OFF & held.

BASELINE = night_hot.bsl
DELAY FOR 60

# Night check on day 1
WHENEVER 1-22:00:00 WHILE enabled("RaiseLightBehavior")
  WAIT FOR 6900
  WAIT led FOR 300
  ENSURE led FOR 1800
  PRINT "LED ON during night at %s (led=%d)" %(clock_time(time), led)

# Morning shutoff on day 2
WHENEVER 2-06:00:00 WHILE enabled("RaiseLightBehavior")
  WAIT not led FOR 900
  ENSURE not led FOR 1800
  PRINT "LED OFF in morning at %s (led=%d)" %(clock_time(time), led)

QUIT AT 2-23:59:59