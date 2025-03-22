from mavsdk import System


# connect to drone system
class Drone:
    def __init__(self):
        self.connection_mavlink = None
        self.connection = None
        self.camera = None

    def setup(self):
        self.init_control()
        self.init_camera()

    def init_control(self):
        self.connection = System()

    def init_camera(self):
        self.camera

    def get_current_frame(self):
        return None


if __name__ == "__main__":
    programm = Drone()
