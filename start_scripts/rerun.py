from payloadcomputerdroneprojekt.image_analysis import ImageAnalysis
import argparse
import os
import json
import cv2
import tempfile
from os.path import join


def main(path, config):
    with open(config) as f:
        config = json.load(f)

    config["image"]["path"] = tempfile.mkdtemp(prefix="precalc_", dir=path)
    with open(join(config["image"]["path"], "config.json"), "w") as f:
        json.dump(config, f, indent=4)

    ia = ImageAnalysis(config=config["image"], camera=None, comms=None)
    ia.config["save_shape_image"] = True

    with open(join(path, "__data__.json")) as f:
        content = f.read()

        if content.startswith("["):
            data = json.loads(content)
        else:
            data = []
            for line in content.splitlines():
                data.append(json.loads(line))

    for item in data:
        ia._image_sub_routine(
            image=cv2.imread(os.path.join(path, item["raw_image"])),
            position_data=item["image_pos"], height=item["height"]
        )
    ia.get_filtered_objs()


def args():
    parser = argparse.ArgumentParser(
        description="This script reruns the image analysis "
        "for the given mission file path.")
    parser.add_argument(
        "path", type=str,
        help="Path to the folder containing the images and __data__.json")
    parser.add_argument("--config", type=str,
                        help="Path to the config file",
                        default=os.path.join(os.path.dirname(__file__),
                                             "config_px4.json"))
    return parser.parse_args()


if __name__ == "__main__":
    a = args()
    print(a.path, a.config)
    main(a.path, a.config)
