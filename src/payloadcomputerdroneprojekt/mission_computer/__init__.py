from payloadcomputerdroneprojekt.communications import Communications
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
from payloadcomputerdroneprojekt.camera import Camera


class MissionComputer():
    def __init__(self, config: dict, port: str, camera: Camera,
                 communications=Communications, image_analysis=ImageAnalysis):
        self._comms = communications(port)

        self._image = image_analysis(
            camera(config.get("camera", None)), self._comms)
        self.config = config

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
