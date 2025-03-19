import unittest
from main_sitl import MainSITL


class TestMain(unittest.TestCase):
    def test_ex1(self):
        program = MainSITL()
        program.setup()


if __name__ == '__main__':
    unittest.main()
