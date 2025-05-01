from payloadcomputerdroneprojekt.camera import Camera
from payloadcomputerdroneprojekt.communications import Communications
import os
import cv2
FILE_PATH = os.path.split(os.path.abspath(__file__))[0]


class TestCamera(Camera):
    def __init__(self, config):
        super().__init__(config)
        self.current = -1
        self.path = os.path.join(FILE_PATH, "test_data")
        self.files = [f for f in os.listdir(self.path)
                      if os.path.isfile(os.path.join(self.path, f))]

    def start_camera(self):
        pass

    def get_current_frame(self):
        self.current += 1
        if self.current >= len(self.files):
            self.current = 0
        return cv2.imread(os.path.join(self.path, self.files[self.current]))


class TestCommunications(Communications):
    def __init__(self, address):
        super().__init__(address)

    def connect(self):
        pass

    def get_position_latlonalt(self):
        return [0, 0, 0, 0, 0, 0]
