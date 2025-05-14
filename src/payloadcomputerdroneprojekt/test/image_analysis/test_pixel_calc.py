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

    def test_local_coords_pos2_0_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 176,
            "y_center": 124
        }
        pos_com = [
            0, 0, 0, 2.5, 0, 0
        ]
        height = 0.83
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == -0.06
        assert pos[1] == -0.16

    def test_local_coords_pos3_0_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 299,
            "y_center": 391
        }
        pos_com = [
            0, 0, 0, -4, 0, 0
        ]
        height = 0.83
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == -0.065
        assert pos[1] == 0.065

    def test_local_coords_pos1_10_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 407,
            "y_center": 319
        }
        pos_com = [
            0, 0, 0, 0, 10, 0
        ]
        height = 0.83
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == 0.15
        assert pos[1] == 0

    def test_local_coords_pos2_10_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 182,
            "y_center": 348
        }
        pos_com = [
            0, 0, 0, 0, 10, 0
        ]
        height = 0.83
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == 0.05
        assert pos[1] == 0.03

    def test_local_coords_pos3_10_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 297,
            "y_center": 255
        }
        pos_com = [
            0, 0, 0, 2.5, 10, 0
        ]
        height = 0.83
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == 0.055
        assert pos[1] == 0.05

    def test_local_coords_pos4_10_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 369,
            "y_center": 425
        }
        pos_com = [
            0, 0, 0, 2.5, 10, 0
        ]
        height = 0.83
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == -0.115
        assert pos[1] == 0.1

    def test_local_coords_pos1_30_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 360,
            "y_center": 319
        }
        pos_com = [
            0, 0, 0, 0, 30, 0
        ]
        height = 0.84
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == -0.15
        assert pos[1] == 0

    def test_local_coords_pos2_30_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 220,
            "y_center": 225
        }
        pos_com = [
            0, 0, 0, 2.5, 30, 0
        ]
        height = 0.84
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == 0.02
        assert pos[1] == -0.09

    def test_local_coords_pos3_30_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 289,
            "y_center": 367
        }
        pos_com = [
            0, 0, 0, 2.5, 30, 0
        ]
        height = 0.84
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == -0.055
        assert pos[1] == -0.055

    def test_local_coords_pos4_30_degree(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 342,
            "y_center": 375
        }
        pos_com = [
            0, 0, 0, 2.5, 30, 0
        ]
        height = 0.84
        pos = ia.add_latlonalt(obj, pos_com, height, (480, 640))
        assert pos[0] == -0.12
        assert pos[1] == -0.06


if __name__ == '__main__':
    unittest.main()
