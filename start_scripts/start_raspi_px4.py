from payloadcomputerdroneprojekt import MissionComputer
from payloadcomputerdroneprojekt.camera import RaspiCamera
import argparse
import os
import json


def main(config, mission):
    mission = os.path.abspath(mission)
    with open(config) as f:
        config = json.load(f)
    port = "serial:///dev/ttyAMA0:115200"
    computer = MissionComputer(config=config, camera=RaspiCamera, port=port)
    computer.initiate(mission)
    computer.start()


def args():
    parser = argparse.ArgumentParser(
        description="This is the start script for the Raspberry Pi 5 with PX4")
    parser.add_argument("mission", type=str, help="Path to the mission file",
                        default="")
    parser.add_argument("--config", type=str,
                        help="Path to the config file",
                        default=os.path.join(os.path.dirname(__file__),
                                             "config_px4.json"))

    return parser.parse_args()


if __name__ == "__main__":
    a = args()
    print(a.config)

    main(a.config, a.mission)
