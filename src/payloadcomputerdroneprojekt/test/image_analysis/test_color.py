import unittest
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import os
import cv2
import tempfile
import json
from payloadcomputerdroneprojekt.test.image_analysis.helper \
    import TestCommunications, TestCamera, FILE_PATH


class TestImage(unittest.TestCase):
    def test_compute_image(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config_2.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))
        image = cv2.imread(os.path.join(
            FILE_PATH, "static_image", "test_exp_00000050.jpg"))

        ia._image_sub_routine(image, [1, 1, 1, 1, 1, 1], 1)

        item = ia._data_handler.list[0].get_dict()["found_objs"]
        assert len(item) == 3
        red = 0
        yellow = 0
        blue = 0
        for i in item:
            if i["color"] == "red":
                red += 1
            elif i["color"] == "yellow":
                yellow += 1
            elif i["color"] == "blue":
                blue += 1
        assert red == 1
        assert yellow == 1
        assert blue == 1


if __name__ == '__main__':
    unittest.main()
