from mavsdk import System


# connect to drone system
class Main:
    def __init__(self):
        self.connection = None
        self.camera = None

    def setup(self):
        self.init_control()
        self.init_camera()

    def init_control(self):
        self.connection = System()

    def init_camera(self):
        self.camera


if __name__ == "__main__":
    programm = Main()
