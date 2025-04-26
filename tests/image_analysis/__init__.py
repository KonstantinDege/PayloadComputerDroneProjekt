import time
import unittest
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
from payloadcomputerdroneprojekt.camera import Camera
from payloadcomputerdroneprojekt.communications import Communications
import os
import cv2
import tempfile
import json
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
        return [], []


class TestImage(unittest.TestCase):
    def test_fps(self):
        """
        Tests if the function could achive the realistic computation time
        """
        time_start = time.time()
        count = 0

        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))

        for _ in cam.files:
            ia.image_loop()
            count += 1
        delta_time = time.time() - time_start
        print(f"Computation Time: {delta_time / count:.2f}")
        assert delta_time / count < 0.3

    def test_color(self):
        """
        Tests if the function gets correct color
        """
        pass

    def test_object_detection(self):
        """
        Tests if the function detects correct objects
        """
        pass

    def test_object_position(self):
        """
        Tests if the function calculates the correct position of the object
        """
        pass

    def test_quality_image(self):
        """
        Tests if the function detects the usability of image correctly
        """
        image = cv2.imread(os.path.join(
            FILE_PATH, "test_data", "artifical_1.jpg"))
        assert 50 < ImageAnalysis.quality_of_image(image) < 60

    def test_compute_image(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, Communications(""))
        image = cv2.imread(os.path.join(
            FILE_PATH, "test_data", "artifical_1.jpg"))

        obj, _ = ia.compute_image(image)

        assert len(obj) == 4

    def test_image_loop(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))

        ia.image_loop()


if __name__ == '__main__':
    unittest.main()
