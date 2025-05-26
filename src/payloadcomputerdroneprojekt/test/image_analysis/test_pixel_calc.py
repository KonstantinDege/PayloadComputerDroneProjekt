from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import unittest
import os
import json
import numpy as np
from payloadcomputerdroneprojekt.test.image_analysis.helper import FILE_PATH


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
            0, 0, 0
        ]
        height = 1
        pos = ia.get_local_offset(obj, pos_com, height, (460, 650))
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
            0, 0, 0
        ]
        height = 1
        pos = ia.get_local_offset(obj, pos_com, height, (460, 650))
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
            0, 0, 0
        ]
        height = 1
        pos = ia.get_local_offset(obj, pos_com, height, (460, 650))
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
            0, 0, 0
        ]
        height = 1
        pos = ia.get_local_offset(obj, pos_com, height, (460, 650))
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
            0, 0, 0
        ]
        height = 1
        pos = ia.get_local_offset(obj, pos_com, height, (460, 650))
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
            0, 0, 0
        ]
        height = 712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[1], 0)
        assert pos[0] > 0

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
            0, 10, 0
        ]
        height = 1
        pos = ia.get_local_offset(obj, pos_com, height, (460, 650))

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
            5, 0, 0
        ]
        height = 1
        pos = ia.get_local_offset(obj, pos_com, height, (460, 650))
        assert pos[0] == 0
        assert pos[1] < 0

    def test_local_coords_image_1(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2298,
            "y_center": 1922
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0.120, places=1)
        self.assertAlmostEqual(pos[1], 0, places=1)

    def test_local_coords_image_2(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2316,
            "y_center": 916
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], -0.080, places=0)
        self.assertAlmostEqual(pos[1], 0, places=2)

    def test_local_coords_image_3(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2067,
            "y_center": 1343
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0, places=1)
        self.assertAlmostEqual(pos[1], 0.050, places=2)

    def test_local_coords_image_4(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2646,
            "y_center": 1353
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0, places=1)
        self.assertAlmostEqual(pos[1], -0.070, places=2)

    def test_local_coords_image_5(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2201,
            "y_center": 1683
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0.070, places=1)
        self.assertAlmostEqual(pos[1], 0.020, places=1)

    def test_local_coords_image_6(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2636,
            "y_center": 1547
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0.040, places=1)
        self.assertAlmostEqual(pos[1], -0.070, places=1)

    def test_local_coords_image_7(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2494,
            "y_center": 1015
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], -0.070, places=1)
        self.assertAlmostEqual(pos[1], -0.040, places=2)

    def test_local_coords_image_8(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2031,
            "y_center": 1223
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], -0.025, places=1)
        self.assertAlmostEqual(pos[1], 0.055, places=2)

    def test_local_coords_image_9(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2312,
            "y_center": 2563
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0.240, places=1)
        self.assertAlmostEqual(pos[1], 0, places=2)

    def test_local_coords_image_10(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 99,
            "y_center": 1371
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0, places=1)
        self.assertAlmostEqual(pos[1], 0.460, places=1)

    def test_local_coords_image_11(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 70,
            "y_center": 2554
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0.240, places=1)
        self.assertAlmostEqual(pos[1], 0.460, places=1)

    def test_local_coords_image_12(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2124,
            "y_center": 1964
        }
        pos_com = [
            0, -15.5, 0
        ]
        height = 0.740
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], -0.070, places=1)
        self.assertAlmostEqual(pos[1], 0.040, places=2)

    def test_local_coords_image_13(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2124,
            "y_center": 1521
        }
        pos_com = [
            0, -8, 0
        ]
        height = 0.725
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], -0.070, places=1)
        self.assertAlmostEqual(pos[1], 0.040, places=2)

    def test_local_coords_image_14(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 4390,
            "y_center": 198
        }
        pos_com = [
            0, -15.5, 0
        ]
        height = 0.712
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], -0.510, places=1)
        self.assertAlmostEqual(pos[1], -0.500, places=1)

    def test_offset(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        config["camera_offset"] = [0.05, 0, 0]
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2304,
            "y_center": 1296
        }
        pos_com = [
            0, 0, 0
        ]
        height = 1
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0.05, places=3)
        self.assertAlmostEqual(pos[1], 0, places=2)

    def test_offset_reduced_height(self):
        with open(os.path.join(FILE_PATH, "test_config.json")) as json_data:
            config = json.load(json_data)["image"]
        config["rotation_offset"] = [0, 0, 180]
        config["path"] = "."
        config["camera_offset"] = [0.05, 0, 0]
        ia = ImageAnalysis(config, "", "")

        obj = {
            "x_center": 2304,
            "y_center": 1296
        }
        pos_com = [
            0, 0, 0
        ]
        height = 0.5
        pos = ia.get_local_offset(obj, pos_com, height, (2592, 4608))
        self.assertAlmostEqual(pos[0], 0.05, places=3)
        self.assertAlmostEqual(pos[1], 0, places=2)


if __name__ == '__main__':
    unittest.main()
