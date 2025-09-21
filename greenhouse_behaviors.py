from behavior import *
from limits import *
from transitions import Machine

#sensor data passed into greenhouse behaviors:
#  [time, lightlevel, temperature, humidity, soilmoisture, waterlevel]
#actuators are looking for a dictionary with any/all of these keywords:
#  {"led":val, "fan":True/False, "pump": True/False}

# A very basic class, so we don't have to declare enable and disable every time
class Greenhouse_Behavior(Behavior):
    def __init__(self, agent, name):
        super(Greenhouse_Behavior, self).__init__(agent, name)    
        
    def enable(self):  self.trigger('enable')
    def disable(self): self.trigger('disable')

'''
The combined ambient and LED light level between 8am and 10pm should be 
in the optimal['light_level'] range;
Between 10pm and 8am, the LEDs should be off (set to 0).
'''
class Light(Greenhouse_Behavior):

    def __init__(self, agent):
        super(Light, self).__init__(agent, "LightBehavior")
        self.optimal_level = optimal['light_level']

        self.initial = 'Halt'
        self.states = [self.initial, 'Init', 'Day', 'Dark']

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)
        
        self.fsm.add_transition('enable', 'Halt', 'Init', after='setInitial')
        self.fsm.add_transition('disable', '*', 'Halt', after='turnOffLED')
        self.fsm.add_transition('doStep', 'Init', 'Day', conditions='is_day')
        self.fsm.add_transition('doStep', 'Init', 'Dark', conditions='is_night')
        self.fsm.add_transition('doStep', 'Day', 'Dark', conditions='is_night', after='turnOffLED')
        self.fsm.add_transition('doStep', 'Dark', 'Day', conditions=['is_day','below_lower'], after='increaseLED')
        self.fsm.add_transition('doStep', 'Dark', 'Day', conditions=['is_day','above_upper'], after='decreaseLED')
        self.fsm.add_transition('doStep', 'Dark', 'Day', conditions='is_day')
        self.fsm.add_transition('doStep', 'Day', 'Day', conditions='below_lower', after='increaseLED')
        self.fsm.add_transition('doStep', 'Day', 'Day', conditions='above_upper', after='decreaseLED')

    def setInitial(self):
        self.led = 0
        self.setLED(self.led)
        
    def perceive(self):
        self.mtime = self.sensordata["midnight_time"]
        self.time = self.sensordata["unix_time"]
        self.light = self.sensordata["light"]
    
    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")
        
    # Add all your condition functions here
    def is_day(self):
        return 8 <= ((self.mtime//3600) % 24) < 22
    
    def is_night(self):
        return not self.is_day()
    
    def below_lower(self):
        return self.light < self.optimal_level[0]
    
    def above_upper(self):
        return self.light >= self.optimal_level[1]
        
    # Add all your before / after action functions here
    def turnOffLED(self):
        self.setLED(0)

    def increaseLED(self):
        self.setLED(self.led+20)

    def decreaseLED(self):
        self.setLED(self.led-20)

    def setLED(self, level):
        self.led = max(0, min(255, level))
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"led": self.led}))
                                  

"""
The temperature should be greater than the lower limit
"""
class RaiseTemp(Greenhouse_Behavior):

    def __init__(self, agent):
        super(RaiseTemp, self).__init__(agent, "RaiseTempBehavior")

        self.initial = 'Halt'
        self.states = [self.initial, 'Init', 'Low', 'Perfect']
        
        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)
        
        self.fsm.add_transition('enable', 'Halt', 'Init', after='setInitial')
        self.fsm.add_transition('disable', '*', 'Halt', after='ledOff')
        self.fsm.add_transition('doStep', 'Init', 'Low', conditions='is_cold', after='setLED200')
        self.fsm.add_transition('doStep', 'Init', 'Perfect', conditions='is_warm')
        self.fsm.add_transition('doStep', 'Low', 'Perfect', conditions='is_warm', after='ledOff')
        self.fsm.add_transition('doStep', 'Perfect', 'Low', conditions='is_cold', after='setLED200')

    def setInitial(self):
        self.setLED(0)
        
    def perceive(self):
        self.temp = self.sensordata["temp"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    def is_cold(self):
        return self.temp <= limits['temperature'][0]
    
    def is_warm(self):
        return self.temp >= optimal['temperature'][0]

    # Add all your before / after action functions here
    def setLED200(self):
        self.setLED(200)
    
    def ledOff(self):
        self.setLED(0)
            
    def setLED(self, level):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"led": level}))
        
"""
The temperature should be less than the upper limit
"""
class LowerTemp(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerTemp, self).__init__(agent, "LowerTempBehavior")

        self.initial = 'Halt'
        self.states = [self.initial, 'Init', 'High', 'Perfect']

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)
        
        self.fsm.add_transition('enable', 'Halt', 'Init', after='setInitial')
        self.fsm.add_transition('disable', '*', 'Halt', after='fanOff')
        self.fsm.add_transition('doStep', 'Init', 'High', conditions='is_hot', after='fanOn')
        self.fsm.add_transition('doStep', 'Init', 'Perfect', conditions='is_cool')
        self.fsm.add_transition('doStep', 'High', 'Perfect', conditions='is_cool', after='fanOff')
        self.fsm.add_transition('doStep', 'Perfect', 'High', conditions='is_hot', after='fanOn')

    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.temp = self.sensordata["temp"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    def is_hot(self):
        return self.temp >= limits['temperature'][1]
    
    def is_cool(self):
        return self.temp <= optimal['temperature'][1]
        
    # Add all your before / after action functions here
    def fanOn(self):
        self.setFan(True)

    def fanOff(self):
        self.setFan(False)
            
    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))
    
"""
Humidity should be less than the limit
"""
class LowerHumid(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerHumid, self).__init__(agent, "LowerHumidBehavior")

        self.initial = 'Halt'
        self.states = [self.initial, 'Init', 'Humid', 'Perfect']

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        self.fsm.add_transition('enable', 'Halt', 'Init', after='setInitial')
        self.fsm.add_transition('disable', '*', 'Halt', after='fanOff')
        self.fsm.add_transition('doStep', 'Init', 'Humid', conditions='is_humid', after='fanOn')
        self.fsm.add_transition('doStep', 'Init', 'Perfect', conditions='is_ok')
        self.fsm.add_transition('doStep', 'Humid', 'Perfect', conditions='is_ok', after='fanOff')
        self.fsm.add_transition('doStep', 'Perfect', 'Humid', conditions='is_humid', after='fanOn')
        
    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.humid = self.sensordata["humid"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    def is_humid(self):
        return self.humid >= limits['humidity'][1]
    
    def is_ok(self):
        return self.humid <= optimal['humidity'][1]
        
    # Add all your before / after action functions here
    def fanOn(self):
        self.setFan(True)

    def fanOff(self):
        self.setFan(False)

    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))
            
"""
Soil moisture should be greater than the lower limit
"""
class RaiseSMoist(Greenhouse_Behavior):

    def __init__(self, agent):
        super(RaiseSMoist, self).__init__(agent, "RaiseMoistBehavior")
        self.weight = 0
        self.weight_window = []
        self.smoist_window = []
        self.total_water = 0
        self.water_level = 0
        self.start_weight = 0
        self.last_time = 24*60*60 # Start with the prior day
        self.daily_limit = 100
        self.wet = limits["moisture"][1]

        self.initial = 'Halt'
        self.states = [self.initial, 'Init', 'Wait', 'Water', 'Measure', 'Done']

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        self.fsm.add_transition('enable', 'Halt', 'Init', after='setInitial')
        self.fsm.add_transition('disable', '*', 'Halt', after='onDisable')
        self.fsm.add_transition('doStep', 'Init', 'Init', conditions='is_next_day', after='resetWater')
        self.fsm.add_transition('doStep', 'Init', 'Wait', conditions='timer_up')
        self.fsm.add_transition('doStep', 'Done', 'Init', conditions='is_next_day', after='setLastTime')
        self.fsm.add_transition('doStep', 'Wait', 'Done', conditions='hit_limit', after='setLastTime')
        self.fsm.add_transition('doStep', 'Wait', 'Done', conditions='reservoir_low', after='setLastTime')
        self.fsm.add_transition('doStep', 'Wait', 'Done', conditions='soil_wet', after='setLastTime')
        self.fsm.add_transition('doStep', 'Wait', 'Water', conditions='should_water', after='startWater')
        self.fsm.add_transition('doStep', 'Water', 'Measure', conditions='timer_up', after='stopAndSettle')
        self.fsm.add_transition('doStep', 'Measure', 'Wait', conditions='timer_up', after='waterAdded')

    def setInitial(self):
        self.setPump(False)
        self.setTimer(10)

    def onDisable(self):
        self.setPump(False)
        self.setLastTime()
        
    def sliding_window(self, window, item, length=4):
        if (len(window) == length): window = window[1:]
        window.append(item)
        return window, sum(window)/float(len(window))
    
    def perceive(self):
        self.time = self.sensordata["unix_time"]
        self.mtime = self.sensordata["midnight_time"]
        self.water_level = self.sensordata["level"]
        self.weight = self.sensordata["weight"]
        self.weight_window, self.weight_est = self.sliding_window(self.weight_window, self.weight)
        self.smoist = self.sensordata["smoist"]
        self.smoist_window, self.smoist_est = self.sliding_window(self.smoist_window, self.smoist)

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    def is_next_day(self):
        return self.last_time > self.mtime
    
    def timer_up(self):
        return hasattr(self, 'waittime') and (self.time >= self.waittime)
    
    def hit_limit(self):
        return self.total_water >= self.daily_limit
    
    def reservoir_low(self):
        return self.water_level < 30
    
    def soil_wet(self):
        return self.smoist_est >= self.wet
    
    def should_water(self):
        return True
    
    # helpers
    def setTimer(self, wait):
        self.waittime = self.time+wait

    def setPump(self,state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"wpump": state}))
        
    def setLastTime(self):
        self.last_time = self.mtime

    def resetWater(self):
        self.total_water = 0
        self.setLastTime()
        
    # Add all your before / after action functions here
    def startWater(self):
        self.start_weight = self.weight_est
        self.setTimer(10)
        self.setPump(True)

    def stopAndSettle(self):
        self.setPump(False)
        self.setTimer(300)

    def waterAdded(self):
        self.total_water = self.total_water + max(0, self.weight_est-self.start_weight)


"""
Soil moisture below the upper limit
"""
class LowerSMoist(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerSMoist, self).__init__(agent, "LowerMoistBehavior")

        self.initial = 'Halt'
        self.states = [self.initial, 'Init', 'Moist', 'Perfect']

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        self.fsm.add_transition('enable', 'Halt', 'Init', after='setInitial')
        self.fsm.add_transition('disable', '*', 'Halt', after='fanOff')
        self.fsm.add_transition('doStep', 'Init', 'Moist', conditions='is_moist', after='fanOn')
        self.fsm.add_transition('doStep', 'Init', 'Perfect', conditions='is_ok')
        self.fsm.add_transition('doStep', 'Moist', 'Perfect', conditions='is_ok', after='fanOff')
        self.fsm.add_transition('doStep', 'Perfect', 'Moist', conditions='is_moist', after='fanOn')
        
    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.smoist = self.sensordata["smoist"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    def is_moist(self):
        return self.smoist >= limits['moisture'][1]
    
    def is_ok(self):
        return self.smoist <= optimal['moisture'][1]
        
    # Add all your before / after action functions here
    def fanOn(self):
        self.setFan(True)

    def fanOff(self):
        self.setFan(False)

    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))
