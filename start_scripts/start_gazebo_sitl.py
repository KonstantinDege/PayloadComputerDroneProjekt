from payloadcomputerdroneprojekt.mission_computer import MissionComputer
from payloadcomputerdroneprojekt.test.image_analysis import TestCamera
import argparse
import os
import json
import asyncio


async def run_cam(computer: MissionComputer):
    await computer._comms.connect()
    computer._image.start_cam()
    while True:
        await asyncio.sleep(2)


async def fligh(computer: MissionComputer):
    con = computer._comms
    await con.connect()
    await con.start()
    print("start checkpoint")
    await con.mov_by_xyz([0, -15, 0])
    print("first checkpoint")
    await con.mov_to_xyz([0, 0, -5])
    await con.land()


async def fligh_cam(computer: MissionComputer):
    con = computer._comms
    await con.connect()
    computer._image.start_cam()
    await con.start()
    print("start checkpoint")
    await con.mov_by_xyz([0, -15, 0])
    print("first checkpoint")
    await con.mov_to_xyz([0, 0, -5])
    await con.land()
    computer._image.stop_cam()


def main(config, mission):
    with open(config) as f:
        config = json.load(f)
    port = "udp://:14540"
    computer = MissionComputer(config=config, camera=TestCamera, port=port)
    if mission == "demo_cam":
        asyncio.run(run_cam(computer))
    elif mission == "fligh":
        asyncio.run(fligh(computer))
    elif mission == "fligh_cam":
        asyncio.run(fligh_cam(computer))
    else:
        computer.start(mission)


def args():
    parser = argparse.ArgumentParser(
        description="This is the start script for the Raspberry Pi 5 with PX4")
    parser.add_argument("mission", type=str, help="Path to the mission file")
    parser.add_argument("--config", type=str,
                        help="Path to the config file",
                        default=os.path.join(os.path.dirname(__file__),
                                             "config_px4.json"))

    return parser.parse_args()


if __name__ == "__main__":
    a = args()
    print(a.config)

    main(a.config, a.mission)
