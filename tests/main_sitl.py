# this file is for the whole SITL loop tests and should override the camera
# bindings as well as connect to the QGroundControl Station instead of using
# the Pi5


from payloadcomputerdroneprojekt.main import Main


class MainSITL(Main):
    def __init__(self):
        super().__init__()

    def init_control(self):
        pass

    def init_camera(self):
        pass
