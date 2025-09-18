from behavior import *
from greenhouse_behaviors import Greenhouse_Behavior
from transitions import Machine
import os, os.path as op

'''
The behavior should adjust the lights to a reasonable level (say 400-600),
wait a bit for the light to stabilize, and then request an image.
It should check to be sure the image has been recorded and, if so, process
the image; if not, try again for up to 3 times before giving up
'''
class TakeImage(Greenhouse_Behavior):
    def __init__(self, agent):
        super(TakeImage, self).__init__(agent, "TakeImageBehavior")
        # Your code here
	# Initialize the FSM and add transitions
        # BEGIN STUDENT CODE
        # END STUDENT CODE

    # Add the condition and action functions
    #  Remember: if statements only in the condition functions;
    #            modify state information only in the action functions
    # BEGIN STUDENT CODE
    # END STUDENT CODE

    def perceive(self):
        self.time = self.sensordata['unix_time']
        # Add any sensor data variables you need for the behavior
        # BEGIN STUDENT CODE
        # END STUDENT CODE

    def act(self):
        self.trigger("doStep")
