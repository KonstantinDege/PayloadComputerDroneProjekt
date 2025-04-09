import time
import unittest
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis


class TestImage(unittest.TestCase):
    def test_fps(self):
        """
        Tests if the function could achive the realistic computation time
        """
        time_start = time.time()
        for x in images:
            ImageAnalysis.get_current_offset_closest(x)
        delta_time = time.time() - time_start
        assert delta_time / len(images) < 0.3


if __name__ == '__main__':
    unittest.main()
