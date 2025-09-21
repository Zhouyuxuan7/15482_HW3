import schedule as sched

class Layer:
    def __init__(self, agent):
        self.agent = agent

    def doStep(self, t=0):
        print("doStep NYI")

class BehavioralLayer(Layer):

    def __init__(self, sensors, actuators, behaviors, agent):
        self.behaviors = behaviors
        for behavior in behaviors:
            behavior.setSensors(sensors)
            behavior.setActuators(actuators)
        self.enabled = []
        super(BehavioralLayer, self).__init__(agent)
        # Initialize any extra variables here

    def getBehavior(self, name):
        for b in self.behaviors:
            if (b.name == name): return b
        return None

    def isEnabled(self, behavior):
        return behavior in self.enabled

    def startBehavior(self,name):
        # BEGIN STUDENT CODE
        behavior = self.getBehavior(name)
        if behavior and not self.isEnabled(behavior):
            behavior.start()
            self.enabled.append(behavior)
        # END STUDENT CODE
        pass

    def pauseBehavior(self,name):
        # BEGIN STUDENT CODE
        behavior = self.getBehavior(name)
        if behavior and self.isEnabled(behavior):
            behavior.pause()
            self.enabled.remove(behavior)
        # END STUDENT CODE
        pass

    def doStep(self):
        for behavior in self.enabled:
            behavior.doStep()

    def startAll(self):
        for behavior in self.behaviors:
            self.startBehavior(behavior.name)

    #more functions? write them here!
    # BEGIN SANITIZE ALL
    # END SANITIZE ALL

class ExecutiveLayer(Layer):

    def __init__(self, agent):
        self.schedule = {}
        self.laststep = -1
        self.monitors = []
        super(ExecutiveLayer, self).__init__(agent)
        # Initialize any extra variables here
        # BEGIN SANITIZE ALL
        self.enabledBehaviors = []
        # END SANITIZE ALL

    def setSchedule(self, schedule):
        self.schedule = schedule

    def requestNewSchedule(self):
        self.agent.getPlanningLayer().requestNewSchedule()

    def getMonitor(self, name):
        for m in self.monitors:
            if (m.name == name): return m
        return None

    def setMonitors(self, sensors, actuator_state, monitorsList):
        self.monitors = monitorsList
        now = sensors.getTime()
        for monitor in self.monitors:
            monitor.setSensors(sensors)
            monitor.setActuatorState(actuator_state)
            monitor.setExecutive(self)
            monitor.last_time = now
            monitor.dt = 0
            monitor.activate()

    def doStep(self, t): #t time in seconds since midnight
        # NOTE: Disable any behaviors that need to be disabled
        #   before enabling any new behaviors
        # BEGIN STUDENT CODE
        currTimeInMins = t / 60
        # First disable any behaviors that need to be disabled
        for behavior, times in self.schedule.items():
            if (behavior in self.enabledBehaviors):
                stillEnabled = False
                for startTime, endTime in times:
                    if startTime <= currTimeInMins and currTimeInMins < endTime:
                        stillEnabled = True
                        break
                if (not stillEnabled):
                    self.enabledBehaviors.remove(behavior)
                    self.agent.getBehavioralLayer().pauseBehavior(behavior)

        # Now enable any behaviors
        for behavior, times in self.schedule.items():
            if (not behavior in self.enabledBehaviors):
                for startTime, endTime in times:
                    if startTime <= currTimeInMins and currTimeInMins < endTime:
                        self.enabledBehaviors.append(behavior)
                        self.agent.getBehavioralLayer().startBehavior(behavior)
                        break
        # END STUDENT CODE
        for monitor in self.monitors:
            monitor.doMonitor()


class PlanningLayer(Layer):

    def __init__(self, schedulefile, agent):
        self.schedulefile = schedulefile
        self.usetestfile = False
        self.schedulerequested = True
        self.schedule = {}
        self.laststep = 0
        super(PlanningLayer, self).__init__(agent)

    def setTestingSchedule(self, testschedule):
        self.testschedule = testschedule

    def switch_to_test_sched(self):
        self.usetestfile = True
        self.requestNewSchedule()

    def getNewSchedule(self):
        scheduleFile = self.testschedule if self.usetestfile else self.schedulefile
        self.schedule = self.scheduleFromFile(scheduleFile)
        self.agent.getExecutiveLayer().setSchedule(self.schedule)
        self.schedulerequested = False

    def requestNewSchedule(self):
        self.schedulerequested = True

    def doStep(self, t):
        if self.schedulerequested or self.checkEnded(t):
            self.getNewSchedule()
        self.laststep = (t//60)%(24*60)

    def checkEnded(self, t):
        mins = (t//60)%(24*60)
        if mins < self.laststep: #looped back around
            return True
        return False

    def scheduleFromFile(self, scheduleFile):
        print(f"Reading schedule from {scheduleFile}")
        return sched.readSchedule(scheduleFile)
