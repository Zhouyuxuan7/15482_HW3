from behavior import *
from transitions import Machine
from greenhouse_behaviors import Greenhouse_Behavior
import send_email

'''
The behavior should send an email that includes the team name and TerraBot
number, the date and time, the current sensor and actuator readings, and
the most recent image taken
'''
class Email(Greenhouse_Behavior):
    def __init__(self, agent):
        super(Email, self).__init__(agent, "EmailBehavior")
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

