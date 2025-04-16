import time
import unittest
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis

IMAGES = ""


class TestImage(unittest.TestCase):
    def test_fps(self):
        """
        Tests if the function could achive the realistic computation time
        """
        time_start = time.time()
        for image in IMAGES:
            ImageAnalysis.get_current_offset_closest(image)
        delta_time = time.time() - time_start
        assert delta_time / len(IMAGES) < 0.3


if __name__ == '__main__':
    unittest.main()
