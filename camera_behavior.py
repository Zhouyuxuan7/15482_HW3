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
        # Track image counts and timing
        self.today_images = 0
        self.last_image_day = -1
        self.current_day = -1   
        self.image_path = None
        self.light_wait_start = None
        self.image_wait_start = None
        self.retry_wait_start = None
        self.retry_count = 0
        self.led = 0

        # FSM States
        self.states = [
            'Halt', 'Adjust', 'WaitLight',
            'RequestImage', 'WaitImage', 'Retry',
            'Success', 'Failure'
        ]

        # FSM Initialization
        self.fsm = Machine(self, states=self.states, initial='Halt',
                           ignore_invalid_triggers=True)

        # --- FSM Transitions ---
        self.fsm.add_transition('enable', 'Halt', 'Adjust', conditions='can_take_image')

        # Adjust LED until light within range
        self.fsm.add_transition('doStep', 'Adjust', 'Adjust',
                                conditions='too_dim', after='increase_light')
        self.fsm.add_transition('doStep', 'Adjust', 'Adjust',
                                conditions='too_bright', after='decrease_light')
        self.fsm.add_transition('doStep', 'Adjust', 'WaitLight',
                                conditions='light_adjusted', after='wait_light')

        # Wait for stabilization
        self.fsm.add_transition('doStep', 'WaitLight', 'RequestImage',
                                conditions='wait_light_finished')

        # Request image immediately, then wait for it
        self.fsm.add_transition('doStep', 'RequestImage', 'WaitImage',
                                after='request_image')

        # Success
        self.fsm.add_transition('doStep', 'WaitImage', 'Success',
                                conditions=['wait_image_finished', 'image_found'],
                                after='update_today_images')

        # Failure after 3 retries
        self.fsm.add_transition('doStep', 'WaitImage', 'Failure',
                                conditions=['wait_image_finished', 'image_not_found', 'retry_count_geq3'])

        # Retry if <3 attempts
        self.fsm.add_transition('doStep', 'WaitImage', 'Retry',
                                conditions=['wait_image_finished', 'image_not_found', 'retry_count_l3'],
                                after=['wait_for_retry', 'update_retry_count'])
        self.fsm.add_transition('doStep', 'Retry', 'RequestImage',
                                conditions='wait_retry_finished')

        # Wrap up
        self.fsm.add_transition('doStep', 'Success', 'Halt', after='reset')
        self.fsm.add_transition('doStep', 'Failure', 'Halt', after='reset')
        self.fsm.add_transition('disable', '*', 'Halt', after='reset')

    # Condition Functions
    def can_take_image(self):
        """
        Allow at most 3 images per day.
        Uses midnight_time reset detection.
        """
        if self.last_image_day != self.current_day:
            print(f"[DEBUG] New day detected! Resetting counter. (prev_day={self.last_image_day}, current_day={self.current_day})")
            self.today_images = 0
            self.last_image_day = self.current_day
        print(f"[DEBUG] can_take_image check: today_images={self.today_images}, current_day={self.current_day}")
        return self.today_images < 3
        
        # current_midnight = self.sensordata['midnight_time']
        # # Detect wrap-around at midnight
        # if self.last_image_day > current_midnight:
        #     print("[DEBUG] New day detected. Resetting daily image count.")
        #     self.today_images = 0
        # self.last_image_day = current_midnight
        # print(f"[DEBUG] can_take_image check: today_images={self.today_images}, "
        #       f"midnight_time={current_midnight}")
        # return self.today_images < 3

    def too_dim(self):
        return self.light < 400

    def too_bright(self):
        return self.light > 600

    def light_adjusted(self):
        return 400 <= self.light <= 600

    def wait_light_finished(self):
        return (self.light_wait_start is not None
                and (self.time - self.light_wait_start) >= 5)

    def wait_image_finished(self):
        return (self.image_wait_start is not None
                and (self.time - self.image_wait_start) >= 10)

    def image_found(self):
        return self.image_path is not None and op.exists(self.image_path)

    def image_not_found(self):
        return self.image_path is None or not op.exists(self.image_path)

    def wait_retry_finished(self):
        return (self.retry_wait_start is not None
                and (self.time - self.retry_wait_start) >= 20)

    def retry_count_l3(self):
        return self.retry_count < 3

    def retry_count_geq3(self):
        return self.retry_count >= 3

    # Action Functions
    def increase_light(self):
        self.setLED(self.led + 40)
        print(f"[DEBUG] Increasing LED to {self.led} (light={self.light})")

    def decrease_light(self):
        self.setLED(self.led - 40)
        print(f"[DEBUG] Decreasing LED to {self.led} (light={self.light})")

    def wait_light(self):
        self.light_wait_start = self.time
        print(f"[DEBUG] Light stabilized. Waiting at time={self.time}")

    def request_image(self):
        """Send camera request and create output directory if needed."""
        dir_path = "/home/robotanist/TerraBot/images"
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"[DEBUG] Created image directory: {dir_path}")

        filename = f"image_{int(self.time)}.jpg"
        self.image_path = os.path.join(dir_path, filename)

        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"camera": self.image_path}))
        self.image_wait_start = self.time
        print(f"[DEBUG] Requested image: {self.image_path} at time={self.time}")

    def update_today_images(self):
        self.today_images += 1
        self.retry_count = 0
        print(f"[DEBUG] Image saved! today_images={self.today_images}")

    def wait_for_retry(self):
        self.retry_wait_start = self.time
        print(f"[DEBUG] Waiting 20s before retry #{self.retry_count + 1}")

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
        self.last_image_day = self.current_day

    # Helper
    def setLED(self, level):
        self.led = max(0, min(255, level))
        self.actuators.doActions(
            (self.name, self.sensors.getTime(), {"led": self.led})
        )
        
    # Perceive / Act
    def perceive(self):
        self.time = self.sensordata['unix_time']
        self.light = self.sensordata['light']
        SECONDS_IN_A_DAY = 24 * 60 * 60
        self.current_day = int(self.sensordata['unix_time'] // SECONDS_IN_A_DAY)

    def act(self):
        print(f"[DEBUG] STATE={self.state}, time={self.time}, light={self.light}, "
              f"today_images={self.today_images}, retry_count={self.retry_count}")
        self.trigger("doStep")
