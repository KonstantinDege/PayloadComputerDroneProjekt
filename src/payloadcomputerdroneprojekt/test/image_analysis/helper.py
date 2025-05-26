from payloadcomputerdroneprojekt.camera import AbstractCamera
from payloadcomputerdroneprojekt.communications import Communications
import os
import cv2
FILE_PATH = os.path.split(os.path.abspath(__file__))[0]


class TestCamera(AbstractCamera):
    def __init__(self, config):
        super().__init__(config)
        self.current = -1
        self.path = os.path.join(FILE_PATH, "test_data")
        self.files = [f for f in os.listdir(self.path)
                      if os.path.isfile(os.path.join(self.path, f))]

    def start_camera(self, config=None):
        pass

    def get_current_frame(self):
        self.current += 1
        if self.current >= len(self.files):
            self.current = 0
        return cv2.imread(os.path.join(self.path, self.files[self.current]))

    def stop_camera(self):
        pass


class TestCommunications(Communications):
    def __init__(self, address):
        super().__init__(address)

    def connect(self):
        pass

    async def get_position_lat_lon_alt(self):
        return [1, 1, 1, 0, 0, 0]

    async def get_relative_height(self):
        return 1
