from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import argparse
import os
import json
import cv2
import tempfile


def main(path, config):
    with open(config) as f:
        config = json.load(f)

    config["image"]["path"] = tempfile.mkdtemp(prefix="precalc_", dir=path)
    ia = ImageAnalysis(config=config["image"], camera=None, comms=None)
    with open(os.path.join(path, "__data__.json")) as f:
        data = json.load(f)
    for item in data:
        ia._image_sub_routine(
            image=cv2.imread(os.path.join(path, item["raw_path"])),
            pos_com=item["image_pos"], height=item["height"]
        )


def args():
    parser = argparse.ArgumentParser(
        description="This is the start script for the Raspberry Pi 5 with PX4")
    parser.add_argument("path", type=str, help="Path to the mission file")
    parser.add_argument("--config", type=str,
                        help="Path to the config file",
                        default=os.path.join(os.path.dirname(__file__),
                                             "config_px4.json"))
    return parser.parse_args()


if __name__ == "__main__":
    a = args()
    print(a.path, a.config)
    main(a.path, a.config)
