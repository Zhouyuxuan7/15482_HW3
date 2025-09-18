WHENEVER 01-23:59:00
  SET target = 8500
  PRINT "INSOLATION TODAY %.1f (vs %.1f)" %(insolation, target)
  # Be within 3% of the target
  ENSURE 0.97*target <= insolation and insolation <= 1.03*target

# Make sure it works for 2 days
QUIT AT 3-00:00:00

