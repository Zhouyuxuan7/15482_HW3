# low_water_level.bsl
# Purpose: Dryish soil but reservoir below safe, to test pump lockout.

start = 1-12:00:00
temperature = 24
humidity = 55
smoist = 300
wlevel = 3           # limits['water_level'][0] = 5
tankwater = 0

wpump = off
fan = off
led = 0

leaf_droop = 0
lankiness = 0
plant_health = 1