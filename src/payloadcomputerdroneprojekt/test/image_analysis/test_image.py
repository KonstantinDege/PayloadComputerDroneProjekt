import time
import unittest
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import os
import cv2
import tempfile
import json
from payloadcomputerdroneprojekt.test.image_analysis.helper \
    import TestCommunications, TestCamera, FILE_PATH
import asyncio
from payloadcomputerdroneprojekt.image_analysis.data_item import DataItem


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
            asyncio.run(ia.image_loop())
            count += 1
        delta_time = time.time() - time_start
        print(f"Computation Time: {delta_time / count:.2f}")
        assert delta_time / count < 0.2

        ia.get_filtered_objs()

    def test_start_camera(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))

        async def com():
            assert ia.start_cam()
        asyncio.run(com())

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
        ia = ImageAnalysis(config, cam, TestCommunications(""))
        image = cv2.imread(os.path.join(
            FILE_PATH, "test_data", "artifical_1.jpg"))

        item = DataItem(path)
        obj, _ = ia.compute_image(image, item)

        assert len(obj) == 3

        ia.get_filtered_objs()

    def test_image_loop(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))

        asyncio.run(ia.image_loop())

        ia.get_filtered_objs()


if __name__ == '__main__':
    unittest.main()
