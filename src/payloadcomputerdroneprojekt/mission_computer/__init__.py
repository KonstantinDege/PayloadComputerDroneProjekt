from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis


class MissionComputer():
    def __init__(self, camera, port,
                 communications=Communications, image_analysis=ImageAnalysis):
        self._comms = communications(port)
        self._image = image_analysis(camera, self._comms)

        self.current_mission_plan = {}

    def start(self, missionfile=""):
        """
        this function starts the computer

        see "Ablaufdiagramm.png"

        parms:
         missionfile: file descriping the mission and it's parameters
                      if not given waiting for Network
        """
        pass
