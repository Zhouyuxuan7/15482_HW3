#BASELINE= # Use a baseline file to start right before an image is to be taken
BASELINE = take_image.bsl

WHENEVER camera != None
  SET image = camera # Do this b/c 'camera' does not stay latched
  PRINT "Waiting for %s" %image
  # If the speedup is high enough, sometimes the camera gets reset before the 
  #  "SET" statement is invoked, which causes "exist" to crash
  WAIT image == None or os.path.exists(image) FOR 10

WHENEVER None != camera # Changed the order to distinguish this from above
  # Test right away
  ENSURE (light > 350 and light < 650) FOR 1

# Count the number of pictures taken
WHENEVER camera != None and True # Do this to distinguish this from above
  SET num_pics = num_pics + 1
# Ensure sure that 3 pictures get taken every day
WHENEVER 1-00:00:00 # Every midnight
  SET daily_pics = num_pics
  WAIT UNTIL 1-23:59:59
  SET dpic = num_pics - daily_pics
  ENSURE dpic == 3

QUIT AT 3-00:10:00
