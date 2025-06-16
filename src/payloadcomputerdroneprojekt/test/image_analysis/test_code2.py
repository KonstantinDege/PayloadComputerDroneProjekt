import unittest
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import os
import cv2
import tempfile
import json
from payloadcomputerdroneprojekt.test.image_analysis.helper \
    import TestCommunications, TestCamera, FILE_PATH


DATA = [
    {"time": 175008095328, "image_pos": [
        0.007329502142965794, 0.013819013722240925, -1.486909031867981,
        -0.43472132086753845, 0.7123400568962097, 0],
     "raw_image": "175008095328_raw_image.jpg", "height": 1.486909031867981},
    {"time": 175008095384, "image_pos": [
        -0.0009770386386662722, 0.02063533291220665, -1.4943788051605225,
        -0.43811672925949097, 0.9459957480430603, 0],
     "raw_image": "175008095384_raw_image.jpg", "height": 1.4943788051605225},
    {"time": 175008095405, "image_pos": [
        0.05918622016906738, 0.009132473729550838, -1.5345736742019653,
        0.9689342975616455, -1.6092430353164673, 0],
     "raw_image": "175008095405_raw_image.jpg", "height": 1.5345736742019653},
    {"time": 175008095436, "image_pos": [
        0.10005003213882446, -0.05298306792974472, -1.2935973405838013,
        2.757206439971924, -2.756244421005249, 0],
     "raw_image": "175008095436_raw_image.jpg", "height": 1.2935973405838013}
]


def calc_offset(ia: ImageAnalysis, image_pos, image, height):
    # Dummy function to simulate offset calculation
    with ia._data_handler as item:
        return ia._get_current_offset_closest(
            image_pos, height, image, "orange", "Code", item=item)


class TestCode2(unittest.TestCase):
    def test_compute_image_3(self):
        path = tempfile.mkdtemp(prefix="image_analysis")
        with open(os.path.join(FILE_PATH, "config_px4.json")) as json_data:
            config = json.load(json_data)["image"]

        config["path"] = path

        cam = TestCamera(config)
        ia = ImageAnalysis(config, cam, TestCommunications(""))
        image = cv2.imread(os.path.join(
            FILE_PATH, "test_land_indoor", "inflight_code.jpg"))
        for data in DATA:
            image_pos = data["image_pos"]
            height = data["height"]
            raw_image_path = os.path.join(
                FILE_PATH, "test_land_indoor", data["raw_image"])
            image = cv2.imread(raw_image_path)
            print(f"Processing image at {raw_image_path}")
            ret = calc_offset(ia, image_pos, image, height)
            print(f"Offset for image {data['raw_image']}: {ret}")


if __name__ == '__main__':
    unittest.main()
