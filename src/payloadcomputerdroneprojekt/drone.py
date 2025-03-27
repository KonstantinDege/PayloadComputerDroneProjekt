class Drone:
    def __init__(self):
        self.connection = None
        self.camera = None

    def setup(self):
        self.init_control()
        self.init_camera()

    def init_control(self):
        raise NotImplementedError("Subclasses need to implement this method")

    def init_camera(self):
        raise NotImplementedError("Subclasses need to implement this method")

    def get_current_frame(self):
        raise NotImplementedError("Subclasses need to implement this method")


if __name__ == "__main__":
    programm = Drone()
