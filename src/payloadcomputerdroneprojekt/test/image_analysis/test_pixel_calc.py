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


if __name__ == '__main__':
    unittest.main()
