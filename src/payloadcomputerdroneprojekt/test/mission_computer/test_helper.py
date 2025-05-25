import unittest
import payloadcomputerdroneprojekt.mission_computer.helper as mc
import json
import os

FILE_PATH = os.path.split(os.path.abspath(__file__))[0]
os.chdir(FILE_PATH)


class TestHelper(unittest.TestCase):
    def test_count(self):
        with open(os.path.join(FILE_PATH, "test_mission.json")) as f:
            mission = json.load(f)
        assert mc.count_actions(mission) == 4

    def test_count_at(self):
        with open(os.path.join(FILE_PATH, "test_mission.json")) as f:
            mission = json.load(f)
        assert mc.action_with_count(mission, 3)["action"] == "list"
        assert len(mc.action_with_count(mission, 3)["commands"]) == 1

    def test_count_at_0(self):
        with open(os.path.join(FILE_PATH, "test_mission.json")) as f:
            mission = json.load(f)
        action = mc.action_with_count(mission, 0)
        assert action["action"] == "list"
        assert len(action["commands"]) == 4

    def test_load_rec(self):
        with open(os.path.join(FILE_PATH, "test_mission_rec.json")) as f:
            mission = json.load(f)
        mc.rec_serialize(mission)
        assert mission["action"] == "list"


if __name__ == "__main__":
    unittest.main()
