from payloadcomputerdroneprojekt.mission_computer import MissionComputer
from payloadcomputerdroneprojekt.camera.gazebo_sitl import GazeboCamera
from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
from payloadcomputerdroneprojekt.communications.helper \
    import rotation_matrix_yaw
from payloadcomputerdroneprojekt.test.image_analysis.helper import FILE_PATH
import numpy as np
import json
import os
import unittest
import asyncio
from random import random


class image(ImageAnalysis):
    def __init__(self, config, camera, comms):
        super().__init__(config, camera, comms)

    async def get_current_offset_closest(self, color, shape,
                                         yaw_0=True, indoor=False):
        cur_pos = await self._comms.get_position_xyz()
        yaw_cur = cur_pos[5]
        cur_pos = np.array(cur_pos[:3])
        pos = (rotation_matrix_yaw(-yaw_cur) @
               cur_pos)[0] * (1+(random()-0.5)/25)
        yaw_target = -90
        await asyncio.sleep(0.5)
        return [-pos[0], -pos[1]], -pos[2], yaw_target - yaw_cur


async def mission():
    port = "udp://:14540"
    with open(os.path.join(FILE_PATH, "test_config_2.json")) as f:
        config = json.load(f)

    config.setdefault("communications", {})["allowed_arm"] = True
    computer = MissionComputer(
        config=config, camera=GazeboCamera, port=port, image_analysis=image)
    computer.current_mission_plan = {
        "parameter": {
            "decision_height": 2
        }
    }
    await computer._comms.connect()

    await computer.takeoff({"height": 15})
    print("takeoff done")
    await computer._comms.mov_by_xyz([4, 5.5, 0], 60)
    print("moved")
    await asyncio.sleep(2)
    await computer.land({"shape": "", "color": ""})


class TestLand(unittest.TestCase):
    def test_land_easy(self):
        asyncio.run(mission())


if __name__ == "__main__":
    unittest.main()
