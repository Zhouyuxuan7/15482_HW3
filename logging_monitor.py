from monitor import *
import logging
import time 
import os

class LoggingMonitor(Monitor):

    def __init__(self, period=10):
        super(LoggingMonitor, self).__init__("LoggingMonitor", period)
        # Put any iniitialization code here
        # BEGIN STUDENT CODE
        log_file = "greenhouse.log"
        if os.path.exists(log_file):
            open(log_file, 'w').close()
        logging.basicConfig(filename="greenhouse.log", level=logging.INFO, format="%(message)s")
        header = "time, light, temp, humid, smoist, weight,level, fan, wpump, camera, led"
        logging.info(header)
        # END STUDENT CODE

    def perceive(self):
        # BEGIN STUDENT CODE
        pass
        # END STUDENT CODE
        

    def monitor(self):
        # Use self.sensorData and self.actuator_state to log the sensor and
        #  actuator data, preferably as a comma-separated line of values.
        #  Make sure to timestamp the line of data
        # BEGIN STUDENT CODE
        timestamp = time.time()  # seconds since epoch
        # Build CSV row
        sensor_values = [str(self.sensordata.get(k, "")) for k in [
            "light", "temp", "humid", "smoist", "weight", "level"
        ]]
        actuator_values = [str(self.actuator_state.get(k, "")) for k in [
            "fan", "wpump", "camera", "led"
        ]]
        row = ",".join([str(timestamp)] + sensor_values + actuator_values)
        logging.info(row)
        # END STUDENT CODE
        pass

