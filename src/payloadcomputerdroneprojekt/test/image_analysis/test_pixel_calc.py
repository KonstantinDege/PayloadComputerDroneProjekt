import unittest.async_case
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import unittest
import os
import json
import numpy as np
from payloadcomputerdroneprojekt.test.image_analysis import FILE_PATH


class TestImage(unittest.TestCase):
    def test_local_coords_0_0(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        # x is camera width
        # but drone forward
        obj = {
            "x_center": 325,
            "y_center": 230
        }
        pos_com = [
            0, 0, 0, 0, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert np.linalg.norm(np.array(pos) - np.array([0, 0, 1])) == 0

    def test_local_coords_pos_x_positive(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 325,
            "y_center": 0
        }
        pos_com = [
            0, 0, 0, 0, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert pos[0] > 0
        assert pos[1] == 0

    def test_local_coords_pos_y_positive(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 600,
            "y_center": 230
        }
        pos_com = [
            0, 0, 0, 0, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert pos[1] > 0
        assert pos[0] == 0

    def test_local_coords_pos_x_negative(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 325,
            "y_center": 400
        }
        pos_com = [
            0, 0, 0, 0, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert pos[0] < 0
        assert pos[1] == 0

    def test_local_coords_pos_y_negative(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 0,
            "y_center": 230
        }
        pos_com = [
            0, 0, 0, 0, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert pos[1] < 0
        assert pos[0] == 0

    def test_local_coords_pos_x_off_pos(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 4608/2,
            "y_center": 2592/2+700
        }
        pos_com = [
            0, 0, 0, 0, 0, 0
        ]
        height = 712
        pos = ia.add_latlonalt(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[1], 0)
        self.assertAlmostEqual(pos[0], 125, places=0)

    def test_local_coords_pitch_angle(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 325,
            "y_center": 230
        }
        pos_com = [
            0, 0, 0, 0, 10, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))

        assert pos[0] > 0
        assert pos[1] == 0

    def test_local_coords_roll_angle(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 325,
            "y_center": 230
        }
        pos_com = [
            0, 0, 0, 5, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert pos[0] == 0
        assert pos[1] < 0


if __name__ == '__main__':
    unittest.main()
