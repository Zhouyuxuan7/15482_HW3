# dry_soil.bsl
# Purpose: Midday, dry soil to trigger watering logic; all actuators initially off.

start = 1-12:00:00
temperature = 24
humidity = 55
smoist = 300
wlevel = 140
tankwater = 60

wpump = off
fan = off
led = 0

leaf_droop = 0
lankiness = 0
plant_health = 1