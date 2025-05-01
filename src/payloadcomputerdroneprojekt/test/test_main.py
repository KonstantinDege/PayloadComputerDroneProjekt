import unittest
from tests.drone_sitl import DroneSITL


class TestMain(unittest.TestCase):
    def test_ex1(self):
        program = DroneSITL()
        program.setup()


if __name__ == '__main__':
    unittest.main()
