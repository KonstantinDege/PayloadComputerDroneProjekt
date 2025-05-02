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

        obj = {
            "x_center": 230,
            "y_center": 325
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
            "x_center": 0,
            "y_center": 325
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
            "x_center": 230,
            "y_center": 600
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
            "x_center": 460,
            "y_center": 325
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
            "x_center": 230,
            "y_center": 0
        }
        pos_com = [
            0, 0, 0, 0, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert pos[1] < 0
        assert pos[0] == 0

    def test_local_coords_pos(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 230,
            "y_center": 325
        }
        pos_com = [
            0, 0, 0, 0, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert pos[1] == 0
        assert pos[0] == 0

    def test_local_coords_pitch_angle(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 230,
            "y_center": 325
        }
        pos_com = [
            0, 0, 0, 0, 10, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))

        self.assertAlmostEqual(
            pos[0], 0 + height * np.tan(np.deg2rad(pos_com[4])), delta=0.0001)
        assert pos[1] == 0

    def test_local_coords_roll_angle(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 230,
            "y_center": 325
        }
        pos_com = [
            0, 0, 0, 5, 0, 0
        ]
        height = 1
        pos = ia.add_latlonalt(obj, pos_com, height, (460, 650))
        assert pos[0] == 0
        self.assertAlmostEqual(
            pos[1], 0 - height * np.tan(np.deg2rad(pos_com[3])), delta=0.0001)
        

if __name__ == '__main__':
    unittest.main()
