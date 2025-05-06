from payloadcomputerdroneprojekt.mission_computer import MissionComputer
from payloadcomputerdroneprojekt.camera.raspi2 import RaspiCamera
import argparse
import os
import json


def main(config):
    with open(config) as f:
        config = json.load(f)
    port = "serial:///dev/ttyAMA0:57600"
    computer = MissionComputer(config=config, camera=RaspiCamera, port=port)
    computer.setup()
    computer.start()


def args():
    parser = argparse.ArgumentParser(
        description="A simple argument parser example.")
    parser.add_argument("mission", type=str, help="Path to the mission file")
    parser.add_argument("--config", type=str,
                        help="Path to the config file",
                        default=os.path.join(os.path.dirname(__file__),
                                             "config_px4.json"))

    return parser.parse_args()


if __name__ == "__main__":
    a = args()
    print(a.config)
    if a.mission == "demo_cam":
        print("starting only cam")
    main()
