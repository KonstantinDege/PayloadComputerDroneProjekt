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

        self.mode = 0
        self.current_mission_plan = {}

    def start(self, mode=0):
        """
        this function starts the computer

        parms:
         mode: 0/1 defines
        """
        pass
