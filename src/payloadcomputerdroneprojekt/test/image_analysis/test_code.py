import unittest
from payloadcomputerdroneprojekt.image_analysis.math_helper \
    import find_relative_position
from itertools import permutations
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import os
import cv2
import tempfile
import json
from payloadcomputerdroneprojekt.test.image_analysis.helper \
    import TestCommunications, TestCamera, FILE_PATH


class TestCode(unittest.TestCase):
    def test_find_orient_1(self):
        p_list = [(-1, 1, 0), (-1, -1, 0), (1, 1, 0)]
        for p_l in permutations(p_list):
            print(p_l)
            o_l, u_l, o_r = find_relative_position(p_l)
            assert o_l[0] == -1
            assert o_l[1] == 1
            assert u_l[0] == -1
            assert u_l[1] == -1
            assert o_r[0] == 1
            assert o_r[1] == 1

    def test_compute_image_code(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config_2.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))
        image = cv2.imread(os.path.join(
            FILE_PATH, "static_image", "Mission_2.png"))
        with ia._data_handler as item:
            ret = ia._get_current_offset_closest(
                [0, 0, 0, 0, 0, 0], 1, image, "orange", "Code", item=item)
        ret[0][0] > 0
        ret[0][1] < 0
        ret[1] > 1
        self.assertAlmostEqual(ret[2], 0)

    def test_compute_image(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config_2.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))
        image = cv2.imread(os.path.join(
            FILE_PATH, "static_image", "mission_3.png"))
        with ia._data_handler as item:
            ret = ia._get_current_offset_closest(
                [0, 0, 0, 0, 0, 0], 1, image, "yellow", "Kreis", item=item)
        print(ret)

    def test_compute_image_2(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "test_config_2.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))
        image = cv2.imread(os.path.join(
            FILE_PATH, "static_image", "small_landing.jpg"))
        with ia._data_handler as item:
            ret = ia._get_current_offset_closest(
                [0, 0, 0, 0, 0, 0], 1, image, "orange", "Code", item=item)
        print(ret)

    def test_compute_image_3(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "config_px4.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))
        image = cv2.imread(os.path.join(
            FILE_PATH, "static_image", "inflight_code.jpg"))
        with ia._data_handler as item:
            ret = ia._get_current_offset_closest(
                [0, 0, 0, 0, 0, 0], 1, image, "orange", "Code", item=item)
        print(f"Code 3: {ret}")


if __name__ == '__main__':
    unittest.main()
