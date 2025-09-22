from behavior import *
from greenhouse_behaviors import Greenhouse_Behavior
from transitions import Machine
import os, os.path as op

class TakeImage(Greenhouse_Behavior):
    '''
    The behavior should adjust the lights to a reasonable level (say 400-600),
    wait a bit for the light to stabilize, and then request an image.
    It should check to be sure the image has been recorded and, if so, process
    the image; if not, try again for up to 3 times before giving up
    '''

    def __init__(self, agent):
        super(TakeImage, self).__init__(agent, "TakeImageBehavior")
        # BEGIN STUDENT CODE
        self.today_images = 0
        self.last_image_day = -1
        self.image_path = None
        self.light_wait_start = None
        self.image_wait_start = None
        self.retry_wait_start = None
        self.retry_count = 0
        self.led = 0
        # --- FSM States ---
        self.states = [
            'Halt', 'Adjust', 'WaitLight',
            'RequestImage', 'WaitImage', 'Retry',
            'Success', 'Failure'
        ]
        # --- Initialize FSM ---
        self.fsm = Machine(
            self, states=self.states, initial='Halt',
            ignore_invalid_triggers=True
        )
        # --- FSM Transitions ---
        self.fsm.add_transition('enable', 'Halt', 'Adjust', conditions='can_take_image')
        # Adjust LED until light within range
        self.fsm.add_transition('doStep', 'Adjust', 'Adjust', conditions='too_dim', after='increase_light')
        self.fsm.add_transition('doStep', 'Adjust', 'Adjust', conditions='too_bright', after='decrease_light')
        self.fsm.add_transition('doStep', 'Adjust', 'WaitLight', conditions='light_adjusted', after='wait_light')
        # Wait for shutter speed to stabilize
        self.fsm.add_transition('doStep', 'WaitLight', 'RequestImage',
                                conditions='wait_light_finished', after='request_image')
        # After request, immediately move to WaitImage
        self.fsm.add_transition('doStep', 'RequestImage', 'WaitImage')
        # Success path
        self.fsm.add_transition('doStep', 'WaitImage', 'Success',
                                conditions=['wait_image_finished', 'image_found'],
                                after='update_today_images')
        # Failure path
        self.fsm.add_transition('doStep', 'WaitImage', 'Failure',
                                conditions=['wait_image_finished', 'image_not_found', 'retry_count_geq3'])
        # Retry path
        self.fsm.add_transition('doStep', 'WaitImage', 'Retry',
                                conditions=['wait_image_finished', 'image_not_found', 'retry_count_l3'],
                                after=['wait_for_retry', 'update_retry_count'])
        self.fsm.add_transition('doStep', 'Retry', 'RequestImage',
                                conditions='wait_retry_finished')
        # Wrap up
        self.fsm.add_transition('doStep', 'Success', 'Halt', after='reset')
        self.fsm.add_transition('doStep', 'Failure', 'Halt', after='reset')
        self.fsm.add_transition('disable', '*', 'Halt', after='reset')
        # END STUDENT CODE

    # Add the condition and action functions
    #  Remember: if statements only in the condition functions;
    #            modify state information only in the action functions
    # BEGIN STUDENT CODE
    # ----------------------------------------------------------------------
    # Condition functions
    # ----------------------------------------------------------------------
    def can_take_image(self):
        """Ensure no more than 3 images are taken per day."""
        current_day = self.sensordata['midnight_time']
        print(f"[DEBUG] can_take_image check: today_images={self.today_images}, "
            f"current_day={current_day}, last_day={self.last_image_day}")
        if self.last_image_day != current_day:
            self.today_images = 0
            self.last_image_day = current_day
            print(f"[DEBUG] New day detected. Resetting today_images to 0.")
        return self.today_images < 3

    def too_dim(self):
        return self.light < 400

    def too_bright(self):
        return self.light > 600

    def light_adjusted(self):
        return 400 <= self.light <= 600

    def wait_light_finished(self):
        return (self.time - self.light_wait_start) >= 5

    def wait_image_finished(self):
        # Spec says wait 10 seconds for file to appear
        return (self.time - self.image_wait_start) >= 10

    def image_found(self):
        return self.image_path is not None and op.exists(self.image_path)

    def image_not_found(self):
        return self.image_path is None or not op.exists(self.image_path)

    def wait_retry_finished(self):
        return (self.time - self.retry_wait_start) >= 20

    def retry_count_l3(self):
        return self.retry_count < 3

    def retry_count_geq3(self):
        return self.retry_count >= 3

    # ----------------------------------------------------------------------
    # Action functions
    # ----------------------------------------------------------------------
    def increase_light(self):
        self.setLED(self.led + 20)
        print(f"[DEBUG] Increasing LED to {self.led} (light={self.light})")

    def decrease_light(self):
        self.setLED(self.led - 20)
        print(f"[DEBUG] Decreasing LED to {self.led} (light={self.light})")

    def wait_light(self):
        self.light_wait_start = self.time
        print(f"[DEBUG] Light stable. Starting stabilization wait at time={self.time}")

    def request_image(self):
        """Send camera request and create output directory if needed."""
        dir_path = "/home/robotanist/TerraBot/images"
        if not os.path.exists(dir_path):
            print(f"[ERROR] Image directory does not exist: {dir_path}")
            self.image_path = None
            return
        filename = f"image_{int(self.time)}.jpg"
        self.image_path = os.path.join(dir_path, filename)

        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"camera": self.image_path}))
        self.image_wait_start = self.time
        print(f"[DEBUG] Requested image: {self.image_path} at time={self.time}")

    def update_today_images(self):
        self.today_images += 1
        self.retry_count = 0  # reset retries on success
        print(f"[DEBUG] Image saved! today_images={self.today_images}")

    def wait_for_retry(self):
        self.retry_wait_start = self.time
        print(f"[DEBUG] Waiting before retry #{self.retry_count + 1}")

    def update_retry_count(self):
        self.retry_count += 1
        print(f"[DEBUG] Retry count updated: {self.retry_count}")

    def reset(self):
        print(f"[DEBUG] Resetting behavior. Final today_images={self.today_images}")
        self.image_path = None
        self.light_wait_start = None
        self.image_wait_start = None
        self.retry_wait_start = None
        self.retry_count = 0
        self.setLED(0)

    # ----------------------------------------------------------------------
    # Helper
    # ----------------------------------------------------------------------
    def setLED(self, level):
        self.led = max(0, min(255, level))
        self.actuators.doActions(
            (self.name, self.sensors.getTime(), {"led": self.led})
        )
    # END STUDENT CODE

    def perceive(self):
        # BEGIN STUDENT CODE
        self.time = self.sensordata['unix_time']
        self.light = self.sensordata['light']
        # END STUDENT CODE

    def act(self):
        print(f"[DEBUG] Current state: {self.state}, time={self.time}, "
              f"light={self.light}, today_images={self.today_images}, retry_count={self.retry_count}")
        self.trigger("doStep")
