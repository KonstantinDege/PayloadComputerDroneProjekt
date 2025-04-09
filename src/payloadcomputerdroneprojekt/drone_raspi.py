# this file is for the whole SITL loop tests and should override the camera
# bindings as well as connect to the QGroundControl Station instead of using
# the Pi5


import drone
from pycamera2 import Pycamera2
from mavsdk import System
import asyncio


class Drone(drone.Drone):
    def __init__(self):
        super().__init__()

    def init_control(self):
        self.connection = System()
        asyncio.run(self.connection.connect(system_address="serial:///dev/ttyAMA0:57600"))
        print("MavSDK established")

    def init_camera(self):
        self.camera = Video()
        print("Camera started")

    def get_current_frame(self):
        while True:
            # Wait for the next frame
            if not self.camera.frame_available():
                continue
            return self.camera.frame()


if __name__ == "__main__":
    drone = Drone()
    drone.setup()
    drone.get_current_frame()
    while True:
        pass
