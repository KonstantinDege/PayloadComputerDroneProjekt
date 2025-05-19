import unittest
import payloadcomputerdroneprojekt.mission_computer as mc
import json


class TestHelper(unittest.TestCase):
    def test_count(self):
        with open("test_mission.json") as f:
            mission = json.load(f)
        mc.count_actions(mission)


if __name__ == "__main__":
    unittest.main()
