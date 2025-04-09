class MissionComputer():
    def __init__(self, drone, comms, image):
        self._drone = drone
        self._comms = comms
        self._image = image
        
        self.mode = 0
        self.current_mission_plan = {}
        pass

    def start(self, mode=0):
        """
        this function starts the computer

        parms:
         mode: 0/1 defines
        """
        pass
