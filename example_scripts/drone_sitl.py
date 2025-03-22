# this file is for the whole SITL loop tests and should override the camera
# bindings as well as connect to the QGroundControl Station instead of using
# the Pi5


from payloadcomputerdroneprojekt.drone import Drone
from cam_v2 import Video
from pymavlink import mavutil
from mavsdk import System
import asyncio


class DroneSITL(Drone):
    def __init__(self):
        super().__init__()

    def init_control(self):
        self.connection_mavlink = mavutil.mavlink_connection(
            "udpin:localhost:14030")

        self.connection_mavlink.wait_heartbeat()
        print("Connection established")

        self.connection = System()
        asyncio.run(self.connection.connect(system_address="udp://:14540"))
        print("MavSDK established")

    def init_camera(self):
        self.camera = Video()
        print("Camera started")

    def get_current_frame(self):
        return self.camera.frame()


if __name__ == "__main__":
    drone = DroneSITL()
    drone.setup()
    drone.get_current_frame()
    while True:
        pass
