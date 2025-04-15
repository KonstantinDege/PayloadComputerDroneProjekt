from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis


class MissionComputer():
    def __init__(self, camera, port,
                 communications=Communications, image_analysis=ImageAnalysis):
        self._comms = communications(port)
        self._image = image_analysis(camera, self._comms)

        self.mode = 0
        self.current_mission_plan = {}

    def start(self, mode=0):
        """
        this function starts the computer

        parms:
         mode: 0/1 defines
        """
        pass
